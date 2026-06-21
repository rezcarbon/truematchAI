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
    # Latin-script: low density of English function words ⇒ probably not English.
    words = [w.lower() for w in _WORD.findall(t)]
    if len(words) < 12:
        return False  # too short to judge a Latin-script language reliably
    marker_ratio = sum(1 for w in words if w in _EN_MARKERS) / len(words)
    return marker_ratio < 0.04


def _normalize(data: dict, original: str) -> dict[str, Any]:
    eng = data.get("english_text")
    if not isinstance(eng, str) or not eng.strip():
        # Model returned nothing usable — never drop the candidate's text.
        return {"source_language": "und", "english_text": original,
                "method": "passthrough-failed", "confidence": 0.0}
    lang = data.get("source_language")
    lang = lang.strip() if isinstance(lang, str) and lang.strip() else "und"
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
    "- Never invent content that is not present in the source."
)


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
        return _normalize(data, original)
    except Exception as exc:  # noqa: BLE001 - translation must never break intake
        logger.warning("Translation failed (%s); using original text", exc.__class__.__name__)
        return {"source_language": "und", "english_text": original,
                "method": "passthrough-error", "confidence": 0.0}
