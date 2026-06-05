"""Semantic / concept-level matcher (Pillar 1) — the independent middle signal.

Operates on the RAW resume and JD text (split into spans), NOT on LLM-extracted
fields, so the score is a deterministic, reproducible function of the source
documents themselves. Static embeddings (model2vec — no torch) catch conceptual
matches a literal keyword scan misses (e.g. "ecosystem brokering" ↔ "built an
innovation ecosystem"); a lexical token-overlap fallback is used when the
embedding model is unavailable. Both paths are deterministic.

Because inputs are the raw documents (which don't change), the same CV+JD always
yields the same score — fixing the run-to-run variance that came from feeding
the matcher non-deterministic LLM extractions.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import settings
from app.engines import text_utils

LEXICAL_METHOD = "lexical-span-v2"
METHOD = LEXICAL_METHOD  # back-compat module attribute

# Cosine rescaling: map a per-span best cosine in [LO, HI] to [0, 1] before
# averaging, so the 0-100 score spreads meaningfully (raw cosines cluster low).
# Calibrated on representative pairs (real matches ~0.5-0.65, non-matches <0.2).
_EMB_LO = 0.15
_EMB_HI = 0.55


@lru_cache(maxsize=1)
def _embedder():
    """Load the static embedding model once. Returns None if unavailable
    (no package / no model cache / offline) → deterministic lexical fallback."""
    if not settings.semantic_use_embeddings:
        return None
    try:
        from model2vec import StaticModel

        return StaticModel.from_pretrained(settings.semantic_embedding_model)
    except Exception:  # noqa: BLE001 - any failure → lexical fallback
        return None


def active_method() -> str:
    """The method that will actually be used (for provenance)."""
    if _embedder() is not None:
        return f"embedding:{settings.semantic_embedding_model}"
    return LEXICAL_METHOD


def _empty(method: str, threshold: float) -> dict[str, Any]:
    return {"score": 0, "method": method, "deterministic": True,
            "matched_concepts": [], "missing_concepts": [], "match_threshold": threshold}


def semantic_score(resume_text: str, jd_text: str) -> dict[str, Any]:
    """Concept-level semantic score (0-100) from the raw CV and JD text."""
    jd_spans = text_utils.sentences(jd_text)
    res_spans = text_utils.sentences(resume_text)
    if not jd_spans:
        return _empty(active_method(), settings.semantic_embedding_threshold)

    embedder = _embedder()
    if embedder is not None and res_spans:
        return _embedding_score(embedder, jd_spans, res_spans)
    return _lexical_score(jd_spans, res_spans)


def _embedding_score(embedder, jd_spans: list[str], res_spans: list[str]) -> dict[str, Any]:
    import numpy as np

    threshold = settings.semantic_embedding_threshold
    jd_vecs = np.asarray(embedder.encode(jd_spans), dtype=float)
    res_vecs = np.asarray(embedder.encode(res_spans), dtype=float)
    jd_n = jd_vecs / (np.linalg.norm(jd_vecs, axis=1, keepdims=True) + 1e-9)
    res_n = res_vecs / (np.linalg.norm(res_vecs, axis=1, keepdims=True) + 1e-9)
    best = (jd_n @ res_n.T).max(axis=1)  # best resume span per JD span

    scaled = np.clip((best - _EMB_LO) / (_EMB_HI - _EMB_LO), 0.0, 1.0)
    score = int(round(100 * float(scaled.mean())))

    order = np.argsort(-best)
    matched = [jd_spans[i][:90] for i in order if best[i] >= threshold][:8]
    missing = [jd_spans[i][:90] for i in order[::-1] if best[i] < threshold][:8]
    return {
        "score": score,
        "method": f"embedding:{settings.semantic_embedding_model}",
        "deterministic": True,
        "matched_concepts": matched,
        "missing_concepts": missing,
        "match_threshold": threshold,
    }


def _lexical_score(jd_spans: list[str], res_spans: list[str]) -> dict[str, Any]:
    """Deterministic token-overlap fallback: a JD span is 'covered' when it shares
    enough content tokens with some resume span."""
    threshold = 0.34
    res_token_sets = [set(text_utils.tokenize(s)) for s in res_spans]
    res_token_sets = [t for t in res_token_sets if t]
    matched: list[str] = []
    missing: list[str] = []
    covered = 0
    for span in jd_spans:
        jt = set(text_utils.tokenize(span))
        if not jt:
            continue
        best = 0.0
        for rt in res_token_sets:
            inter = len(jt & rt)
            if inter:
                best = max(best, inter / len(jt))
        if best >= threshold:
            covered += 1
            matched.append(span[:90])
        else:
            missing.append(span[:90])
    total = covered + len(missing)
    return {
        "score": round(100 * covered / total) if total else 0,
        "method": LEXICAL_METHOD,
        "deterministic": True,
        "matched_concepts": matched[:8],
        "missing_concepts": missing[:8],
        "match_threshold": threshold,
    }
