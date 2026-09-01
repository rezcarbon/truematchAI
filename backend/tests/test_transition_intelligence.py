"""Transition Intelligence: engine grounding contract + runner + endpoint gating."""
from __future__ import annotations

import uuid

import pytest

from app.api.v1 import transition_intelligence as ti_api
from app.core.exceptions import NotFoundError
from app.engines import transition_intelligence as ti
from app.models.resume import Resume
from app.models.transition_analysis import TransitionAnalysis, TransitionStatus
from app.models.user import User, UserRole
from app.schemas.transition_intelligence import TransitionStartRequest

RESUME_TEXT = (
    "Senior engineer. Operated Docker Swarm clusters in production. Built scalable "
    "Python backend services. Led a team of four; owned incident response."
)


@pytest.fixture
def _offline(monkeypatch):
    from app.engines import intake, reasoning, substitution
    from app.engines import transition_intelligence as ti_engine

    for mod in (intake, substitution, reasoning, ti_engine):
        monkeypatch.setattr(mod, "is_live", lambda: False)


# --- engine contract --------------------------------------------------------


def test_normalize_drops_ungrounded_options():
    out = ti._normalize({
        "readiness_summary": "s",
        "transition_options": [
            {"role": "Staff Engineer", "rationale": "scope evidence", "feasibility": "STRETCH",
             "evidence_strength": "MEDIUM",
             "timeline": {"months_min": 12, "months_max": 6, "confidence": "medium", "basis": "b"}},
            {"role": "", "rationale": "", "feasibility": "MAYBE", "evidence_strength": "?"},  # ungrounded
        ],
    })
    assert len(out["transition_options"]) == 1
    assert out["dropped_ungrounded"] == 1
    # timeline min/max get ordered, confidence preserved
    tl = out["transition_options"][0]["timeline"]
    assert tl["months_min"] == 6 and tl["months_max"] == 12


def test_normalize_clamps_and_defaults_timeline():
    out = ti._normalize({
        "transition_options": [
            {"role": "X", "rationale": "r", "feasibility": "READY", "evidence_strength": "HIGH",
             "timeline": {"months_min": -5, "months_max": 999, "confidence": "bogus"}},
        ],
    })
    tl = out["transition_options"][0]["timeline"]
    assert tl["months_min"] == 0 and tl["months_max"] == 120
    assert tl["confidence"] == "low"  # invalid → low


def test_invalid_feasibility_or_strength_is_dropped():
    out = ti._normalize({"transition_options": [
        {"role": "X", "rationale": "r", "feasibility": "READY", "evidence_strength": "BOGUS"},
        {"role": "Y", "rationale": "r", "feasibility": "BOGUS", "evidence_strength": "HIGH"},
    ]})
    assert out["transition_options"] == []
    assert out["dropped_ungrounded"] == 2


# --- runner (offline, real DB) ---------------------------------------------


def test_runner_produces_grounded_options(sync_db_session, _offline):
    db = sync_db_session
    user = User(email=f"cand_{uuid.uuid4()}@t.com", password_hash="h", role=UserRole.candidate)
    db.add(user)
    db.flush()
    resume = Resume(
        user_id=user.id, file_type="pdf",
        parsed_data={"skills": ["Docker Swarm", "Python"], "narrative": "Senior eng."},
        supplementary={"extracted_text": RESUME_TEXT},
    )
    db.add(resume)
    db.flush()
    analysis = TransitionAnalysis(
        user_id=user.id, resume_id=resume.id, current_role="Senior Engineer",
        status=TransitionStatus.pending,
    )
    db.add(analysis)
    db.commit()

    from app.workers.transition_intelligence import run_transition_sync

    run_transition_sync(db, analysis)

    assert analysis.status == TransitionStatus.completed
    result = analysis.result or {}
    opts = result.get("transition_options") or []
    assert opts, "expected at least one grounded option"
    for o in opts:
        assert o["feasibility"] in {"READY", "STRETCH", "ASPIRATIONAL"}
        assert o["evidence_strength"] in {"HIGH", "MEDIUM", "WEAK"}
        assert o["timeline"]["months_min"] <= o["timeline"]["months_max"]
    assert analysis.provenance["method"] == "transition-intelligence-v1"


# --- endpoint gating (FakeAsyncSession, no DB) ------------------------------


class _FakeAsyncSession:
    def __init__(self, objects: dict):
        self._objects = objects
        self.added: list = []

    async def get(self, model, ident):
        obj = self._objects.get(model)
        if obj is not None and getattr(obj, "id", None) == ident:
            return obj
        return self._objects.get((model, ident))

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        for o in self.added:
            if getattr(o, "id", None) is None:
                o.id = uuid.uuid4()

    async def commit(self):
        pass


def _candidate() -> User:
    u = User(email="c@e.com", role=UserRole.candidate)
    u.id = uuid.uuid4()
    return u


@pytest.mark.asyncio
async def test_endpoint_enqueues_and_returns_202(monkeypatch):
    monkeypatch.setattr(ti_api.settings, "transition_intelligence_enabled", True)
    user = _candidate()
    resume = Resume(user_id=user.id, file_type="pdf", supplementary={"extracted_text": "x"})
    resume.id = uuid.uuid4()
    db = _FakeAsyncSession({Resume: resume})

    calls: list[str] = []
    from app.workers import transition_intelligence as worker

    monkeypatch.setattr(worker.process_transition_task, "delay", lambda aid: calls.append(aid))

    resp = await ti_api.start_transition(
        TransitionStartRequest(resume_id=resume.id, current_role="Engineer"), user, db
    )
    assert resp.status == TransitionStatus.pending
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_endpoint_rejects_unknown_resume(monkeypatch):
    monkeypatch.setattr(ti_api.settings, "transition_intelligence_enabled", True)
    user = _candidate()
    db = _FakeAsyncSession({})
    with pytest.raises(NotFoundError):
        await ti_api.start_transition(
            TransitionStartRequest(resume_id=uuid.uuid4(), current_role="X"), user, db
        )


@pytest.mark.asyncio
async def test_endpoint_404_when_disabled(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(ti_api.settings, "transition_intelligence_enabled", False)
    user = _candidate()
    db = _FakeAsyncSession({})
    with pytest.raises(HTTPException) as exc:
        await ti_api.start_transition(
            TransitionStartRequest(resume_id=uuid.uuid4()), user, db
        )
    assert exc.value.status_code == 404
