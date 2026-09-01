"""Semantic matcher tests (Pillar 1) — raw-text spans, deterministic."""
from __future__ import annotations

import pytest

from app.engines import semantic_match

RESUME = (
    "Founder and chief architect. Built an innovation ecosystem connecting founders, "
    "corporates, investors and government from zero, generating over 100 million in value. "
    "Led institutional fundraising and venture building across the region. "
    "Invented an on-device cognitive AI system and filed AI patents."
)


def test_score_is_deterministic_from_raw_text():
    jd = "We need ecosystem brokering across government, industry and research; community building."
    a = semantic_match.semantic_score(RESUME, jd)
    b = semantic_match.semantic_score(RESUME, jd)
    assert a == b  # same raw inputs -> identical result (reproducible/auditable)
    assert 0 <= a["score"] <= 100
    assert a["deterministic"] is True


def test_role_differentiation():
    jd_fit = "Ecosystem development, community building, connecting founders and government, AI."
    jd_unfit = "Architectural design, building construction, MEPF engineering, workplace interiors."
    fit = semantic_match.semantic_score(RESUME, jd_fit)["score"]
    unfit = semantic_match.semantic_score(RESUME, jd_unfit)["score"]
    assert fit > unfit  # the matcher must distinguish a fitting JD from an unfitting one


def test_empty_jd_scores_zero():
    assert semantic_match.semantic_score(RESUME, "")["score"] == 0


def test_lexical_fallback_when_embeddings_off(monkeypatch):
    monkeypatch.setattr(semantic_match.settings, "semantic_use_embeddings", False)
    semantic_match._embedder.cache_clear()
    r = semantic_match.semantic_score(RESUME, "ecosystem and investors and founders and government")
    assert r["method"] == "lexical-span-v2"
    assert r["score"] > 0
    semantic_match._embedder.cache_clear()


def test_embeddings_catch_conceptual_match(monkeypatch):
    pytest.importorskip("model2vec")
    monkeypatch.setattr(semantic_match.settings, "semantic_use_embeddings", True)
    semantic_match._embedder.cache_clear()
    if semantic_match._embedder() is None:
        semantic_match._embedder.cache_clear()
        pytest.skip("embedding model unavailable offline")

    # Almost no literal token overlap, but the concept matches.
    jd = "Steward and broker connections across the technology ecosystem."
    emb = semantic_match.semantic_score(RESUME, jd)
    assert emb["method"].startswith("embedding:")
    assert emb["score"] > 0
    semantic_match._embedder.cache_clear()
