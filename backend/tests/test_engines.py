"""Engine tests in mock mode (A1): structure + validation, no network."""
from __future__ import annotations

from app.core.governance import (
    COHERENCE_THRESHOLD,
    CONSISTENCY_BOUND,
    COUNTER_REC_DELTA,
    FIDELITY_THRESHOLD,
    GovernanceConfig,
)
from app.engines import governance_engine, intake, reasoning
from app.engines.client import _extract_json, is_live


def _cfg() -> GovernanceConfig:
    return GovernanceConfig(
        {
            COHERENCE_THRESHOLD: 0.8,
            CONSISTENCY_BOUND: 0.15,
            FIDELITY_THRESHOLD: 0.9,
            COUNTER_REC_DELTA: 25,
        }
    )


def test_is_live_false_when_forced_mock():
    # conftest sets LLM_FORCE_MOCK=true
    assert is_live() is False


def test_intake_mock_shapes():
    parsed = intake.parse_resume("some resume text", {})
    assert "skills" in parsed and "experience" in parsed
    reqs = intake.analyze_jd("a job description")
    assert "required_capabilities" in reqs


def test_traditional_ats_is_deterministic_and_role_differentiated():
    # Deterministic keyword baseline (no LLM): JD vocabulary present in the resume
    # scores higher than JD vocabulary absent from it.
    resume = "Experienced python backend engineer building distributed systems and kubernetes."
    jd_fit = "Backend engineer with python, distributed systems and kubernetes experience."
    jd_unfit = "Architectural design and building construction with MEPF engineering."
    fit = intake.traditional_ats(jd_fit, resume)
    unfit = intake.traditional_ats(jd_unfit, resume)
    assert fit["method"] == "keyword-tfidf-v1"
    assert fit["deterministic"] is True
    assert fit["score"] > unfit["score"]
    assert intake.traditional_ats(jd_fit, resume) == fit  # reproducible


def test_traditional_ats_idf_upweights_distinctive_terms():
    # A rare/distinctive term (high IDF) present in the resume should lift the
    # score more than a common term (low IDF) — the corpus-learning effect.
    resume = "kubernetes platform engineer"
    jd = "kubernetes experience and management experience"
    idf_distinctive = {"kubernetes": 5.0, "management": 1.0}
    idf_common = {"kubernetes": 1.0, "management": 5.0}
    hi = intake.traditional_ats(jd, resume, idf=idf_distinctive)
    lo = intake.traditional_ats(jd, resume, idf=idf_common)
    assert hi["idf_weighted"] is True
    assert hi["score"] > lo["score"]  # resume matches the high-IDF term


def test_reasoning_mock_shapes():
    cap = reasoning.assess_capability({}, {}, None)
    assert 0 <= cap["score"] <= 100
    assert isinstance(cap["components"], dict)
    traj = reasoning.analyze_trajectory({})
    assert "narrative" in traj
    jd = reasoning.interrogate_jd("jd")
    assert 0 <= jd["quality_score"] <= 100
    counter = reasoning.counter_recommendation({}, cap, {})
    assert "reasoning" in counter


def test_governance_engine_returns_pass_fail_without_measure():
    view = {"capability_score": 81, "components": {}, "narrative": "n"}
    cfg = _cfg()
    coh = governance_engine.check_coherence(view, cfg)
    con = governance_engine.check_consistency(view, cfg)
    fid = governance_engine.check_fidelity({}, view, cfg)
    bias = governance_engine.check_bias({}, view)
    for result in (coh, con, fid):
        assert isinstance(result["passed"], bool)
        # IP-SAFETY: raw numeric measures must never be surfaced.
        assert "measure" not in result
        assert "deviation" not in result
    assert "flags" in bias


def test_extract_json_tolerates_fences_and_prose():
    assert _extract_json('{"a": 1}') == {"a": 1}
    assert _extract_json('```json\n{"a": 2}\n```') == {"a": 2}
    assert _extract_json('Here you go: {"a": 3}. Done.') == {"a": 3}


def test_extract_json_tolerates_control_chars_in_strings():
    # LLMs emit multi-line narrative fields with literal newlines/tabs inside
    # string values — must parse (strict=False) rather than fail the assessment.
    assert _extract_json('{"narrative": "line one\nline two\twith tab"}') == {
        "narrative": "line one\nline two\twith tab"
    }
