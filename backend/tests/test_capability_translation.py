"""Capability Translation: offline runner pipeline + endpoint gating."""
from __future__ import annotations

import uuid

import pytest

from app.api.v1 import capability_translation as ct_api
from app.core.exceptions import NotFoundError
from app.models.capability_translation import CapabilityTranslation, TranslationStatus
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.schemas.capability_translation import TranslationStartRequest

JD = (
    "We need a backend engineer with Kubernetes, Python and distributed systems "
    "experience to design and operate production inference services."
)
RESUME_TEXT = (
    "Senior engineer. Operated Docker Swarm clusters in production. Built scalable "
    "Python backend services handling millions of requests. Led distributed systems design."
)


@pytest.fixture
def _offline(monkeypatch):
    """Force the LLM-backed engines onto their deterministic offline fixtures."""
    from app.engines import capability_translation, intake, reasoning, substitution

    for mod in (intake, substitution, capability_translation, reasoning):
        monkeypatch.setattr(mod, "is_live", lambda: False)


def test_runner_translates_scores_and_grounds(sync_db_session, _offline):
    db = sync_db_session
    user = User(email=f"cand_{uuid.uuid4()}@t.com", password_hash="h", role=UserRole.candidate)
    db.add(user)
    db.flush()
    resume = Resume(
        user_id=user.id,
        file_type="pdf",
        parsed_data={"skills": ["Docker Swarm", "Python"], "education": [{"degree": "BSc CS"}]},
        supplementary={"extracted_text": RESUME_TEXT},
    )
    db.add(resume)
    db.flush()
    translation = CapabilityTranslation(
        user_id=user.id, resume_id=resume.id, target_jd=JD, target_role="Backend Engineer",
        status=TranslationStatus.pending,
    )
    db.add(translation)
    db.commit()

    from app.workers.capability_translation import run_translation_sync

    run_translation_sync(db, translation)

    assert translation.status == TranslationStatus.completed
    # Before/after scores are real ints from the deterministic engines.
    for s in (
        translation.before_keyword_score, translation.after_keyword_score,
        translation.before_semantic_score, translation.after_semantic_score,
    ):
        assert isinstance(s, int) and 0 <= s <= 100

    # No-fabrication contract: every emitted bullet is grounded + strength-tagged.
    bullets = (translation.rewrite or {}).get("bullets") or []
    assert bullets, "expected at least one grounded bullet"
    for b in bullets:
        assert b["grounding"].strip()
        assert b["evidence_strength"] in {"HIGH", "MEDIUM", "WEAK"}

    # Re-scoring used the deterministic engines (provenance records the method).
    assert translation.provenance["translation_method"] == "capability-translation-v1"
    assert translation.score_detail["keyword_after"] is not None


def test_runner_lifts_keyword_score_when_rewrite_adds_legible_terms(sync_db_session, _offline):
    """The rewrite should not score LOWER than the original on keyword match —
    the whole point is measured legibility, not regression."""
    db = sync_db_session
    user = User(email=f"cand_{uuid.uuid4()}@t.com", password_hash="h", role=UserRole.candidate)
    db.add(user)
    db.flush()
    resume = Resume(
        user_id=user.id, file_type="pdf",
        parsed_data={"skills": ["Docker Swarm", "Python", "Kubernetes"]},
        supplementary={"extracted_text": RESUME_TEXT},
    )
    db.add(resume)
    db.flush()
    t = CapabilityTranslation(
        user_id=user.id, resume_id=resume.id, target_jd=JD, status=TranslationStatus.pending
    )
    db.add(t)
    db.commit()

    from app.workers.capability_translation import run_translation_sync

    run_translation_sync(db, t)
    assert t.after_keyword_score >= t.before_keyword_score


# --- endpoint-level (FakeAsyncSession, no DB) -------------------------------


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
    user = _candidate()
    resume = Resume(user_id=user.id, file_type="pdf", supplementary={"extracted_text": "x"})
    resume.id = uuid.uuid4()
    db = _FakeAsyncSession({Resume: resume})

    calls: list[str] = []
    from app.workers import capability_translation as worker

    monkeypatch.setattr(worker.process_translation_task, "delay", lambda tid: calls.append(tid))

    resp = await ct_api.start_translation(
        TranslationStartRequest(resume_id=resume.id, jd_text=JD, target_role="BE"), user, db
    )
    assert resp.status == TranslationStatus.pending
    assert len(calls) == 1  # enqueued exactly once


def test_normalize_tolerates_nonstring_fields():
    """The model sometimes returns dict/list where a string is expected
    (e.g. translation_notes as an object) — _normalize must not crash."""
    from app.engines.capability_translation import _normalize

    out = _normalize({
        "summary": {"headline": "Senior AI leader", "detail": "25 years"},
        "skills": ["Python", {"name": "Kubernetes"}],
        "bullets": [{"text": "Did X", "grounding": "resume", "evidence_strength": "high"}],
        "translation_notes": {"gap": "no TOGAF", "note": "acquire cert"},
    })
    assert isinstance(out["summary"], str) and "Senior AI leader" in out["summary"]
    assert isinstance(out["translation_notes"], str) and "TOGAF" in out["translation_notes"]
    assert out["bullets"][0]["evidence_strength"] == "HIGH"
    assert all(isinstance(s, str) for s in out["skills"])


@pytest.mark.asyncio
async def test_endpoint_rejects_unknown_resume():
    user = _candidate()
    db = _FakeAsyncSession({})
    with pytest.raises(NotFoundError):
        await ct_api.start_translation(
            TranslationStartRequest(resume_id=uuid.uuid4(), jd_text=JD), user, db
        )
