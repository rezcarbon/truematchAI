"""PDPA/GDPR export + erasure endpoint logic (A4 follow-up).

Drives the real endpoint coroutines against a fake async session so the
assembly/erasure logic is verified without a database.
"""
from __future__ import annotations

import uuid

import pytest

from app.api.v1.profile import erase_my_data, export_my_data
from app.models.assessment import Assessment, AssessmentStatus
from app.models.audit import AuditTrail
from app.models.decision import Decision, DecisionOutcome
from app.models.profile import CapabilityProfile, ProfileVisibility
from app.models.resume import Resume
from app.models.user import User, UserRole


class _Result:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


class AsyncFakeSession:
    """Routes scalar/scalars by the select's primary mapped entity."""

    def __init__(self, data: dict):
        self._data = data
        self.added: list = []
        self.deleted: list = []

    @staticmethod
    def _entity(stmt):
        return stmt.column_descriptions[0]["entity"]

    async def scalar(self, stmt):
        items = self._data.get(self._entity(stmt), [])
        return items[0] if items else None

    async def scalars(self, stmt):
        return _Result(self._data.get(self._entity(stmt), []))

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def delete(self, obj):
        self.deleted.append(obj)


def _seed_user() -> User:
    u = User(email="cand@example.com", role=UserRole.candidate, display_name="Cand")
    u.id = uuid.uuid4()
    return u


@pytest.mark.asyncio
async def test_export_assembles_all_user_data():
    user = _seed_user()
    profile = CapabilityProfile(user_id=user.id)
    profile.visibility = ProfileVisibility.private
    profile.narrative = "strong delivery"
    profile.assessment_count = 1
    resume = Resume(
        user_id=user.id,
        file_type="pdf",
        supplementary={"extracted_text": "resume text"},
    )
    resume.id = uuid.uuid4()
    assessment = Assessment(resume_id=resume.id, position_id=uuid.uuid4(), user_id=user.id)
    assessment.id = uuid.uuid4()
    assessment.status = AssessmentStatus.completed
    assessment.capability_score = 81
    decision = Decision(
        assessment_id=assessment.id, position_id=uuid.uuid4(), decision=DecisionOutcome.advance
    )
    decision.id = uuid.uuid4()

    db = AsyncFakeSession(
        {
            CapabilityProfile: [profile],
            Resume: [resume],
            Assessment: [assessment],
            Decision: [decision],
        }
    )

    export = await export_my_data(user, db)

    assert export["format"] == "truematch.data-export.v1"
    assert export["user"]["email"] == "cand@example.com"
    assert export["profile"]["narrative"] == "strong delivery"
    assert export["resumes"][0]["supplementary"]["extracted_text"] == "resume text"
    assert export["assessments"][0]["capability_score"] == 81
    assert export["decisions_made"][0]["decision"] == "advance"


@pytest.mark.asyncio
async def test_export_with_no_profile_is_none():
    user = _seed_user()
    db = AsyncFakeSession({})  # nothing seeded
    export = await export_my_data(user, db)
    assert export["profile"] is None
    assert export["resumes"] == []


@pytest.mark.asyncio
async def test_erasure_writes_tombstone_and_deletes_user():
    user = _seed_user()
    db = AsyncFakeSession({})
    result = await erase_my_data(user, db)
    assert result is None
    # A compliance tombstone (unlinked to any assessment) was written...
    tombstones = [a for a in db.added if isinstance(a, AuditTrail)]
    assert len(tombstones) == 1
    assert tombstones[0].event_type == "user.erased"
    assert tombstones[0].assessment_id is None
    # ...and the user is deleted (cascade handled by the DB).
    assert user in db.deleted
