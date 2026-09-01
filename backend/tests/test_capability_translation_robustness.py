"""Regression: the Capability Translation worker must survive LLM responses that
return nested dicts/lists where strings are expected (the intermittent
`'dict' object has no attribute 'strip'` class of failure).

Every LLM call on the worker path is monkeypatched to emit adversarial,
dict-valued fields; `run_translation_sync` must still complete (not raise).
"""
from __future__ import annotations

import pytest

from app.engines import capability_translation as C
from app.engines import intake as I
from app.engines import reasoning as R
from app.engines import semantic_match as SM
from app.engines import substitution as S
from app.engines import translation as T
from app.workers import capability_translation as W

# Adversarial LLM payloads — string-ish fields returned as nested objects/lists.
_PARSED = {
    "contact": {"name": {"first": "Mo", "last": "R"}},
    "summary": {"text": "summary as object"},
    "narrative": {"text": "narrative as object"},
    "skills": [{"name": "Python"}, "Kubernetes"],
    "experience": [{"title": {"x": "Eng"}, "org": "Acme", "highlights": [{"h": "did x"}]}],
    "education": [{"degree": {"name": "BSc"}, "school": "U"}],
}
_REQS = {
    "required_capabilities": [{"name": "AI"}],
    "proxies": [{"requirement": {"x": "MSc"}, "underlying_capability": {"y": "depth"}}],
}
_SUBS = {"substitutions": [{
    "requirement": {"x": "MSc"}, "substitution_strength": {"v": "HIGH"},
    "underlying_capability": {"y": "depth"}, "alternate_evidence": [{"e": "shipped"}],
    "rationale": {"r": "because"},
}]}
_TRANS = {
    "summary": {"s": "rewritten"}, "skills": [{"k": "Py"}],
    "bullets": [{"text": {"t": "did"}, "grounding": {"g": "resume"}, "evidence_strength": {"e": "HIGH"}}],
    "translation_notes": {"n": "nothing added"},
}
_CAP = {"score": 60, "components": {"domain_depth": {"score": 60, "evidence": {"e": "x"}}}, "narrative": {"n": "v"}}


class _FakeResume:
    id = "r1"
    user_id = "u1"
    supplementary = {"extracted_text": "Senior engineer. Built Python services. Led teams. " * 5}
    raw_narrative = None
    parsed_data = None
    source_language = None


class _FakeTranslation:
    id = "t1"
    resume_id = "r1"
    target_jd = "Need a Python engineer with leadership and AI."
    status = None
    source_language = None
    original_text = None
    rewrite = None
    substitutions = None
    before_keyword_score = after_keyword_score = None
    before_semantic_score = after_semantic_score = capability_score = None
    score_detail = None
    provenance = None


class _FakeDB:
    def __init__(self, resume):
        self._resume = resume

    def get(self, model, ident):
        return self._resume

    def commit(self):
        pass


@pytest.fixture
def _adversarial_llm(monkeypatch):
    for mod in (I, S, R, C, T):
        monkeypatch.setattr(mod, "is_live", lambda: True)

    def _intake_call(**k):
        sysp = (k.get("system") or "").lower()
        return _REQS if ("job description" in sysp or "requirements" in sysp) else _PARSED

    monkeypatch.setattr(I, "call_claude_json", _intake_call)
    monkeypatch.setattr(S, "call_claude_json", lambda **k: _SUBS)
    monkeypatch.setattr(R, "call_claude_json", lambda **k: _CAP)
    monkeypatch.setattr(C, "call_claude_json", lambda **k: _TRANS)
    monkeypatch.setattr(T, "call_claude_json", lambda **k: {
        "english_text": {"oops": "dict"}, "source_language": {"l": "en"}, "confidence": {"c": 1}})
    # Keep the test hermetic + fast (no embedding model / network).
    monkeypatch.setattr(SM, "semantic_score",
                        lambda *a, **k: {"score": 50, "method": "test", "matched_concepts": []})


def test_worker_survives_dict_valued_llm_fields(_adversarial_llm):
    t = _FakeTranslation()
    # Must not raise — the whole point of the no-fabrication coercion contract.
    W.run_translation_sync(_FakeDB(_FakeResume()), t)
    assert t.status.value == "completed"
    assert isinstance(t.before_keyword_score, int)
    assert isinstance(t.after_keyword_score, int)


def test_capability_verdict_survives_dict_valued_fields(_adversarial_llm):
    """Even with a dict-valued narrative/parse, the capability verdict still
    computes (it is fed clean text via the worker's coercion boundary)."""
    t = _FakeTranslation()
    W.run_translation_sync(_FakeDB(_FakeResume()), t)
    assert t.capability_score == 60  # from the (clamped) adversarial _CAP payload
