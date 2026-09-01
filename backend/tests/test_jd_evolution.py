"""JD evolution tests (Pillar 3). Deterministic drift + mock recommendations."""
from __future__ import annotations

from app.engines import jd_evolution
from app.core import provenance


def _v(version, desc, reqs, quality):
    return {
        "version": version,
        "description": desc,
        "parsed_requirements": {"required_capabilities": reqs},
        "jd_quality_score": quality,
    }


def test_single_version_has_no_drift():
    out = jd_evolution.analyze_evolution([_v(1, "5+ years", ["a"], 80)])
    assert out["drift_signals"] == []
    assert out["evolved_requirements_draft"] is None


def test_experience_creep_detected():
    versions = [
        _v(1, "Requires 5+ years experience", ["a"], 75),
        _v(2, "Requires 8+ years experience", ["a", "b"], 70),
    ]
    drift = jd_evolution.detect_drift(versions)
    types = {s["type"] for s in drift["drift_signals"]}
    assert "experience_creep" in types
    assert "scope_expansion" in types  # 1 -> 2 required capabilities


def test_quality_decline_trend():
    versions = [_v(1, "x", ["a"], 85), _v(2, "x", ["a"], 60)]
    drift = jd_evolution.detect_drift(versions)
    assert drift["trend"] == "degrading"
    assert any(s["type"] == "quality_decline" for s in drift["drift_signals"])


def test_analyze_evolution_mock_multi_version():
    versions = [_v(1, "5+ years", ["a"], 75), _v(2, "8+ years", ["a", "b"], 70)]
    out = jd_evolution.analyze_evolution(versions)
    assert out["drift_signals"]  # deterministic signals always present
    assert isinstance(out["recommendations"], list)
    assert out["method"] == "jd-evolution-v1"


def test_provenance_manifest_shape():
    m = provenance.build_manifest("resume text", "jd text")
    assert m["prompt_registry_version"]
    assert m["reasoning_mode"] in {"live", "mock"}
    assert len(m["input_hashes"]["resume_sha256"]) == 64
    assert len(m["input_hashes"]["jd_sha256"]) == 64
    # deterministic: same inputs -> same hashes
    assert provenance.build_manifest("resume text", "jd text") == m
    assert m["deterministic_engines"]["semantic_match"] == "lexical-span-v2"
    assert m["deterministic_engines"]["traditional_ats"] == "keyword-tfidf-v1"
