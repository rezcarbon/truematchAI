"""Credential-substitution engine tests (Pillar 6). Mock mode (no network)."""
from __future__ import annotations

from app.engines import substitution


def test_no_proxies_yields_empty():
    assert substitution.build_substitution_profile([], {"skills": []}) == {"substitutions": []}
    assert substitution.build_substitution_profile(None, {}) == {"substitutions": []}


def test_mock_substitution_shape():
    proxies = [
        {"requirement": "MSc Computer Science", "underlying_capability": "deep technical depth"},
        {"requirement": "8+ years at a tech firm", "underlying_capability": "operating at scale"},
    ]
    result = substitution.build_substitution_profile(proxies, {"skills": ["python"]})
    subs = result["substitutions"]
    assert len(subs) == 2
    for s in subs:
        assert s["substitution_strength"] in {"HIGH", "MEDIUM", "WEAK"}
        assert "underlying_capability" in s
        assert isinstance(s["alternate_evidence"], list)
    # maps the proxy's underlying capability through
    assert subs[0]["underlying_capability"] == "deep technical depth"


def test_evidence_is_accepted_without_network():
    proxies = [{"requirement": "MSc CS", "underlying_capability": "technical depth"}]
    evidence = [
        {"source_type": "github", "ref": "github.com/x/y", "status": "verified",
         "summary": "Repo with 8k stars"},
    ]
    result = substitution.build_substitution_profile(proxies, {}, evidence)
    assert result["substitutions"]  # produced a substitution entry
