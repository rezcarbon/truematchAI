"""Phase 3: longitudinal trajectory + cohort metrics + tracking endpoints."""
from __future__ import annotations

import datetime as dt
import uuid

import pytest

from app.api.v1 import transition_intelligence as ti_api
from app.models.transition_analysis import (
    OutcomeStatus,
    TransitionAnalysis,
    TransitionOutcome,
    TransitionStatus,
)
from app.models.user import User, UserRole
from app.schemas.transition_intelligence import OutcomeRecordRequest, TrackRequest
from app.services import transition_tracking as tt


def _analysis(score, options, created, status=TransitionStatus.completed, track=False, uid=None):
    a = TransitionAnalysis(
        user_id=uid or uuid.uuid4(), resume_id=uuid.uuid4(),
        status=status, capability_score=score, track=track,
        result={"transition_options": options},
    )
    a.id = uuid.uuid4()
    a.created_at = created
    return a


def test_build_trajectory_orders_and_counts():
    t0 = dt.datetime(2026, 1, 1)
    t1 = dt.datetime(2026, 4, 1)
    a_late = _analysis(58, [{"feasibility": "READY", "role": "Lead"},
                            {"feasibility": "STRETCH", "role": "Staff"}], t1)
    a_early = _analysis(47, [{"feasibility": "STRETCH", "role": "Staff"}], t0)
    pts = tt.build_trajectory([a_late, a_early])
    assert [p["capability_score"] for p in pts] == [47, 58]  # oldest → newest
    assert pts[1]["ready"] == 1 and pts[1]["top_role"] == "Lead"


def test_trajectory_skips_incomplete():
    pend = _analysis(0, [], dt.datetime(2026, 2, 1), status=TransitionStatus.analyzing)
    assert tt.build_trajectory([pend]) == []


def test_aggregate_metrics_readiness_and_achievement():
    uid = uuid.uuid4()
    analyses = [
        _analysis(60, [{"feasibility": "READY"}, {"feasibility": "STRETCH"}],
                  dt.datetime(2026, 1, 1), track=True, uid=uid),
        _analysis(64, [{"feasibility": "READY"}, {"feasibility": "ASPIRATIONAL"}],
                  dt.datetime(2026, 4, 1), uid=uid),
    ]
    outcomes = [
        _outcome(OutcomeStatus.achieved), _outcome(OutcomeStatus.achieved),
        _outcome(OutcomeStatus.not_pursued), _outcome(OutcomeStatus.pursuing),
    ]
    m = tt.aggregate_metrics(analyses, outcomes)
    assert m["readiness"] == {"ready": 2, "stretch": 1, "aspirational": 1}
    assert m["tracked"] == 1
    assert m["candidates"] == 1
    assert m["outcomes"]["achieved"] == 2
    assert m["achievement_rate"] == round(2 / 3, 3)  # achieved / (achieved+not_pursued)


def _outcome(status):
    o = TransitionOutcome(user_id=uuid.uuid4(), analysis_id=uuid.uuid4(),
                          predicted_role="X", status=status)
    return o


def test_next_review_uses_interval(monkeypatch):
    monkeypatch.setattr(tt.settings, "transition_reassess_interval_days", 90)
    base = dt.datetime(2026, 1, 1)
    assert tt.next_review_at(base) == base + dt.timedelta(days=90)


# --- endpoints (FakeAsyncSession) ------------------------------------------


class _FakeAsyncSession:
    def __init__(self, objects: dict):
        self._objects = objects
        self.added: list = []

    async def get(self, model, ident):
        return self._objects.get((model, ident))

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def commit(self):
        pass


def _candidate():
    u = User(email="c@e.com", role=UserRole.candidate)
    u.id = uuid.uuid4()
    return u


def _recruiter():
    u = User(email="r@e.com", role=UserRole.recruiter)
    u.id = uuid.uuid4()
    return u


@pytest.mark.asyncio
async def test_set_tracking_enables_review():
    user = _candidate()
    a = _analysis(60, [], dt.datetime(2026, 1, 1), uid=user.id)
    db = _FakeAsyncSession({(TransitionAnalysis, a.id): a})
    resp = await ti_api.set_tracking(a.id, TrackRequest(enabled=True), user, db)
    assert resp["tracking"] is True and a.track is True and a.next_review_at is not None


@pytest.mark.asyncio
async def test_record_outcome_creates_and_validates():
    user = _recruiter()
    a = _analysis(60, [], dt.datetime(2026, 1, 1))
    db = _FakeAsyncSession({(TransitionAnalysis, a.id): a})
    out = await ti_api.record_outcome(
        OutcomeRecordRequest(analysis_id=a.id, predicted_role="Lead", status="achieved",
                             actual_role="Engineering Lead"), user, db)
    assert out.status == "achieved" and out.predicted_role == "Lead"

    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        await ti_api.record_outcome(
            OutcomeRecordRequest(analysis_id=a.id, predicted_role="Lead", status="bogus"), user, db)


@pytest.mark.asyncio
async def test_metrics_requires_staff():
    from fastapi import HTTPException

    db = _FakeAsyncSession({})
    with pytest.raises(HTTPException) as exc:
        await ti_api.get_metrics(_candidate(), db)
    assert exc.value.status_code == 403
