"""Candidate self-serve assessment endpoint (gap closure)."""
from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.api.v1.assessments import create_self_assessment
from app.models.assessment import Assessment
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.schemas.assessment import SelfAssessmentCreate
from app.workers import tasks

JD = "We need a senior ML platform engineer to design and operate inference systems."


class FakeAsyncSession:
    def __init__(self, objects: dict):
        self._objects = objects
        self.added: list = []

    async def get(self, model, ident):
        return self._objects.get(model)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()

    async def commit(self):
        pass


def _user() -> User:
    u = User(email="cand@example.com", role=UserRole.candidate)
    u.id = uuid.uuid4()
    return u


@pytest.fixture
def captured_delay(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(tasks.run_assessment, "delay", lambda aid: calls.append(aid))
    return calls


@pytest.mark.asyncio
async def test_self_assessment_creates_position_and_enqueues(captured_delay):
    user = _user()
    resume = Resume(user_id=user.id, file_type="pdf", supplementary={"extracted_text": "x"})
    resume.id = uuid.uuid4()
    db = FakeAsyncSession({Resume: resume})

    payload = SelfAssessmentCreate(resume_id=resume.id, jd_text=JD, position_title="ML Engineer")
    result = await create_self_assessment(payload, user, db)

    assert isinstance(result, Assessment)
    assert result.user_id == user.id
    # An internal, company-less position was created from the JD.
    position = next(o for o in db.added if isinstance(o, Position))
    assert position.company_id is None
    assert position.created_by == user.id
    assert position.description == JD
    assert position.title == "ML Engineer"
    # The pipeline was enqueued for the new assessment.
    assert captured_delay == [str(result.id)]


@pytest.mark.asyncio
async def test_self_assessment_rejects_other_users_resume(captured_delay):
    user = _user()
    resume = Resume(user_id=uuid.uuid4(), file_type="pdf")  # different owner
    resume.id = uuid.uuid4()
    db = FakeAsyncSession({Resume: resume})
    payload = SelfAssessmentCreate(resume_id=resume.id, jd_text=JD)
    with pytest.raises(HTTPException) as exc:
        await create_self_assessment(payload, user, db)
    assert exc.value.status_code == 403
    assert captured_delay == []


@pytest.mark.asyncio
async def test_self_assessment_missing_resume_404(captured_delay):
    user = _user()
    db = FakeAsyncSession({})  # no resume
    payload = SelfAssessmentCreate(resume_id=uuid.uuid4(), jd_text=JD)
    with pytest.raises(HTTPException) as exc:
        await create_self_assessment(payload, user, db)
    assert exc.value.status_code == 404
