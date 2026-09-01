"""Modular training-provider registry + curated catalog + transition enrichment."""
from __future__ import annotations

from app.services import training
from app.services.training.providers.curated import CuratedCatalogProvider
from app.services.training.providers.ntuc_learninghub import NTUCLearningHubProvider
from app.services.training.registry import enrich_transition_result, recommend_for_capabilities


def test_curated_provider_matches_known_capability():
    p = CuratedCatalogProvider()
    matches = p.match(["People management for a step-up role"], {})
    assert matches, "expected curated catalog to match a leadership gap"
    assert all(m.capability == "People management for a step-up role" for m in matches)
    assert any("leadership" in m.title.lower() or m.provider for m in matches)


def test_curated_provider_no_match_returns_empty():
    p = CuratedCatalogProvider()
    assert p.match(["underwater basket weaving"], {}) == []


def test_partner_stub_is_safe_noop_until_configured(monkeypatch):
    p = NTUCLearningHubProvider()
    assert p.enabled() is False  # default off
    assert p.match(["leadership"], {}) == []


def test_registry_dedups_and_caps(monkeypatch):
    matches = recommend_for_capabilities(
        ["leadership", "stakeholder management"], per_capability_cap=1
    )
    # at most one per capability after the cap
    by_cap: dict[str, int] = {}
    for m in matches:
        by_cap[m.capability.lower()] = by_cap.get(m.capability.lower(), 0) + 1
    assert all(v <= 1 for v in by_cap.values())


def test_recommend_disabled_returns_empty(monkeypatch):
    from app.services.training import registry as reg

    monkeypatch.setattr(reg.settings, "training_recommendations_enabled", False)
    assert recommend_for_capabilities(["leadership"]) == []


def test_enrich_transition_result_attaches_courses():
    result = {
        "transition_options": [
            {
                "role": "Engineering Manager",
                "upskilling_gap": [
                    {"capability": "People management", "why": "scope", "how": "course"},
                    {"capability": "zzz no match zzz", "why": "", "how": ""},
                ],
            }
        ]
    }
    out = enrich_transition_result(result)
    gaps = out["transition_options"][0]["upskilling_gap"]
    assert gaps[0]["recommended_training"], "leadership gap should get recommendations"
    assert gaps[1]["recommended_training"] == []  # no-match capability → empty list
    # each recommendation carries the gap capability + a provider
    rec = gaps[0]["recommended_training"][0]
    assert rec["capability"] == "People management" and rec["provider"]


def test_builtin_providers_registered():
    names = {p.name for p in training.enabled_providers()}
    assert "curated" in names  # always-on built-in
