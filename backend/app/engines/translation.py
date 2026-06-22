"""Language detection + English-pivot translation for multilingual intake.

The platform's deterministic signals (keyword/ATS term-frequency, the corpus IDF)
are English-tokenised. Rather than maintain a tokenizer, stopword list and IDF
corpus per language, non-English résumés and job descriptions are translated to a
faithful **English pivot** at intake; every downstream engine then runs on English
unchanged. The original text is always retained for display and provenance.

Detection is dependency-free:
  * Any meaningful share of NON-LATIN characters (CJK, Kana, Hangul, Devanagari,
    Tamil, Telugu, Bengali, Arabic, Hebrew, Thai, Cyrillic, Greek, …) is decisive —
    the text is not English, so it is translated.
  * Latin-script text is gated by an English-function-word heuristic; the exact
    source language is then confirmed by the translation model itself.

Translation is a mechanical, faithful task, so it runs on the fast model. It never
summarises, omits, or embellishes — consistent with the platform's no-fabrication
discipline. Offline / no-key environments pass the text through unchanged.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.config import settings
from app.engines.client import call_claude_json, is_live

logger = logging.getLogger("truematch.translation")

# Unicode blocks that are unambiguously non-Latin (and therefore non-English).
_NON_LATIN = re.compile(
    "["
    "一-鿿"   # CJK unified ideographs (Chinese / Kanji)
    "぀-ヿ"   # Hiragana + Katakana (Japanese)
    "가-힯"   # Hangul (Korean)
    "ऀ-ॿ"   # Devanagari (Hindi, …)
    "ঀ-৿"   # Bengali
    "஀-௿"   # Tamil
    "ఀ-౿"   # Telugu
    "ഀ-ൿ"   # Malayalam
    "਀-੿"   # Gurmukhi (Punjabi)
    "؀-ۿ"   # Arabic
    "֐-׿"   # Hebrew
    "฀-๿"   # Thai
    "Ѐ-ӿ"   # Cyrillic
    "Ͱ-Ͽ"   # Greek
    "]"
)

# High-frequency English function words — used only to tell English apart from
# other LATIN-script languages (Malay, Indonesian, Spanish, …) cheaply.
_EN_MARKERS = frozenset(
    "the and of to in for with is are a an on as that this be by or at from it "
    "we our your you they will has have not but can".split()
)
# High-frequency function words for the major LATIN-script NON-English languages.
# English-token-heavy résumés (URLs, "AI", company names) can clear the English
# scarcity bar, so we also detect a language *positively* by its own stopwords.
_FOREIGN_LATIN_MARKERS = frozenset(
    # Malay / Indonesian
    "dan yang di ke dari untuk dengan dalam pada adalah ini itu atau akan tidak "
    "kepada oleh sebagai serta juga telah dapat lebih bagi merupakan "
    # Spanish / Portuguese
    "de la el en los las con por para una del se su como más também uma não "
    # French
    "le les des et un une pour avec dans sur qui est aux ses "
    # German
    "und der die das mit für von den im zu ein eine ist auch werden "
    # Italian
    "il di per con che del della gli sono".split()
) - _EN_MARKERS  # drop any overlap so shared tokens don't double-count
_WORD = re.compile(r"[A-Za-z]+")


def _non_latin_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    non_latin = sum(1 for c in letters if _NON_LATIN.match(c))
    return non_latin / len(letters)


def likely_non_english(text: str) -> bool:
    """Cheap, deterministic gate: is this text worth translating?"""
    t = (text or "").strip()
    if len(t) < 8:
        return False
    # Decisive: a non-trivial share of non-Latin script.
    if _non_latin_ratio(t) > 0.10:
        return True
    # Latin-script: weigh English function-word density against the density of
    # NON-English Latin function words.
    words = [w.lower() for w in _WORD.findall(t)]
    if len(words) < 12:
        return False  # too short to judge a Latin-script language reliably
    n = len(words)
    en_ratio = sum(1 for w in words if w in _EN_MARKERS) / n
    foreign_ratio = sum(1 for w in words if w in _FOREIGN_LATIN_MARKERS) / n
    # English is scarce ⇒ not English; OR a non-English language asserts itself
    # (its stopwords are common AND outweigh English markers). The second clause
    # catches English-token-heavy résumés that clear the scarcity bar.
    return en_ratio < 0.04 or (foreign_ratio >= 0.05 and foreign_ratio > en_ratio)


def _first_str(data: dict, *keys: str) -> str | None:
    """Return the first key whose value is a non-empty string (key-alias tolerant)."""
    for k in keys:
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def _iter_strings(obj: Any):
    """Yield every string value anywhere in a nested dict/list payload."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_strings(v)


def _normalize(data: dict, original: str) -> dict[str, Any]:
    # The model is free-form inside the forced-tool `data` object, so it may name
    # the translation `translated_text`/`translation`/`text` rather than
    # `english_text`. Accept the common aliases so a key-name drift never silently
    # disables the pivot (this exact mismatch shipped a no-op once).
    eng = _first_str(data, "english_text", "translated_text", "translation",
                     "english", "text", "output", "result", "content")
    if eng is None:
        # The forced-tool `data` object is free-form, so the model occasionally
        # names the field something none of the aliases catch (or nests it). The
        # translation is by far the longest string in the payload — fall back to
        # it so a key-name drift can NEVER silently disable the pivot. (A pure
        # alias list once shipped a no-op; this guarantees the pivot survives.)
        strings = [v.strip() for v in _iter_strings(data) if isinstance(v, str) and v.strip()]
        longest = max(strings, key=len, default="")
        eng = longest if len(longest) >= 20 else None
    if eng is None:
        # Genuinely nothing usable — never drop the candidate's text.
        return {"source_language": "und", "english_text": original,
                "method": "passthrough-failed", "confidence": 0.0}
    lang = _first_str(data, "source_language", "detected_language", "language", "lang") or "und"
    lang = lang.strip()
    if len(lang) > 12:  # a sentence, not an ISO code — don't trust it as a language
        lang = "und"
    try:
        conf = float(data.get("confidence"))
    except (TypeError, ValueError):
        conf = 0.0
    return {"source_language": lang, "english_text": eng.strip(),
            "method": "llm", "confidence": max(0.0, min(1.0, conf))}


_SYSTEM = (
    "You are a faithful translation engine for a hiring-assessment platform. You "
    "receive a résumé or job description that may be in any language. Detect the "
    "source language and produce a COMPLETE, faithful English translation.\n"
    "Rules:\n"
    "- Translate everything; do NOT summarise, omit, reorder, add, or embellish.\n"
    "- Preserve proper nouns (people, companies, schools), job titles, technical "
    "terms, product names, numbers, dates and acronyms; transliterate names where "
    "there is no standard English form.\n"
    "- If the text is already English, return it unchanged with source_language 'en'.\n"
    "- Never invent content that is not present in the source.\n"
    "Return JSON with EXACTLY these keys: source_language (ISO 639-1 code, e.g. 'zh', "
    "'ja', 'ms', 'ta', or 'en'); confidence (number 0-1); english_text (the COMPLETE "
    "English translation as a single string)."
)


# Malay vs Indonesian are mutually intelligible, so an LLM detector routinely
# labels Indonesian as "ms". These are high-precision minimal pairs (same concept,
# different word) plus the diagnostic suffix split (-iti in Malay vs -itas in
# Indonesian) — enough to correct the label deterministically from the text.
_MS_MARKERS = frozenset(
    "perkhidmatan kewangan syarikat maklumat pengurusan kemahiran pejabat kerana "
    "wang jawatan universiti aktiviti kualiti majoriti boleh".split()
)
_ID_MARKERS = frozenset(
    "keuangan layanan perusahaan manajemen informasi kantor keterampilan karena "
    "uang jabatan universitas aktivitas kualitas mayoritas bisa".split()
)
_MALAY_FAMILY = {"ms", "msa", "may", "zsm", "malay", "id", "in", "ind", "indonesian"}
_ITI = re.compile(r"\b\w+iti\b")     # universiti, aktiviti, kualiti  (Malay)
_ITAS = re.compile(r"\b\w+itas\b")   # universitas, aktivitas, kualitas (Indonesian)


def refine_malay_indonesian(text: str, detected: str | None) -> str:
    """Disambiguate Malay (ms) from Indonesian (id) when the detector returns the
    Malay-family. Returns the corrected ISO code; falls back to the input when the
    text gives no signal either way."""
    d = (detected or "").strip().lower()
    if d not in _MALAY_FAMILY:
        return detected or "und"
    words = [w.lower() for w in _WORD.findall(text)]
    ms = sum(1 for w in words if w in _MS_MARKERS) + len(_ITI.findall(text))
    idn = sum(1 for w in words if w in _ID_MARKERS) + len(_ITAS.findall(text))
    if idn > ms:
        return "id"
    if ms > idn:
        return "ms"
    # No distinguishing evidence — normalise the detector's own guess.
    return "id" if d in {"id", "in", "ind", "indonesian"} else "ms"


def to_english(text: str, *, kind: str = "document") -> dict[str, Any]:
    """Return an English pivot for ``text``.

    Returns ``{source_language, english_text, method, confidence}``. English (or
    empty) input passes through untouched; non-English input is translated by the
    fast model. Any failure degrades safely to passing the original through, so
    intake never fails on a translation problem.
    """
    original = text or ""
    if not original.strip():
        return {"source_language": "und", "english_text": original,
                "method": "empty", "confidence": 0.0}
    if not likely_non_english(original):
        return {"source_language": "en", "english_text": original,
                "method": "passthrough", "confidence": 1.0}
    if not is_live():
        # No model available (tests / offline): keep the original so the pipeline
        # still runs, flagged so provenance shows it was not translated.
        return {"source_language": "und", "english_text": original,
                "method": "passthrough-offline", "confidence": 0.0}
    try:
        data = call_claude_json(
            system=_SYSTEM,
            user_content=f"Document type: {kind}.\n\nText to translate:\n{original}",
            max_tokens=8192,
            model=settings.anthropic_fast_model,
        )
        result = _normalize(data, original)
        if result["method"] == "llm":
            result["source_language"] = refine_malay_indonesian(original, result["source_language"])
        return result
    except Exception as exc:  # noqa: BLE001 - translation must never break intake
        logger.warning("Translation failed (%s); using original text", exc.__class__.__name__)
        return {"source_language": "und", "english_text": original,
                "method": "passthrough-error", "confidence": 0.0}
