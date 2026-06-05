"""Docker-backed end-to-end pipeline test against a real PostgreSQL.

Verifies the production driver path (psycopg v3 sync), real JSONB/enum/UUID
columns, and the full run_assessment orchestration writing to a real database.

Skipped automatically when Docker/testcontainers are unavailable (e.g. local
machines without Docker). Runs in CI where Docker is present.
"""
from __future__ import annotations

import uuid

import pytest

testcontainers = pytest.importorskip("testcontainers.postgres")
from testcontainers.postgres import PostgresContainer  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


@pytest.fixture(scope="module")
def pg_url():
    try:
        with PostgresContainer("postgres:16-alpine", driver="psycopg") as pg:
            yield pg.get_connection_url()
    except Exception as exc:  # Docker not running / image pull blocked
        pytest.skip(f"Docker/testcontainers unavailable: {exc}")


def test_full_pipeline_against_real_postgres(pg_url, monkeypatch):
    import base64

    from app.core import crypto

    # Turn ON field-level encryption so we can assert ciphertext-at-rest.
    monkeypatch.setattr(crypto.settings, "encryption_key", base64.b64encode(b"K" * 32).decode())
    crypto._dek.cache_clear()
    crypto._index_key.cache_clear()

    from app.database import Base
    from app.models.assessment import Assessment, AssessmentStatus
    from app.models.audit import AuditTrail  # noqa: F401 - ensure table registered
    from app.models.company import Company  # noqa: F401
    from app.models.corpus import CorpusTermStat  # noqa: F401 - ensure table registered
    from app.models.jd_version import JDVersion  # noqa: F401 - ensure table registered
    from app.models.position import Position
    from app.models.profile import CapabilityProfile  # noqa: F401
    from app.models.resume import Resume
    from app.models.user import User
    from app.workers import tasks

    engine = create_engine(pg_url, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    # Point the worker's lazy session factory at this engine.
    monkeypatch.setattr(tasks, "_SyncSessionLocal", SessionLocal)
    monkeypatch.setattr(tasks, "_sync_engine", engine)

    # Ungoverned run (placeholder governance) -> completes with mock scores.
    from app.core.governance import (
        COHERENCE_THRESHOLD,
        CONSISTENCY_BOUND,
        COUNTER_REC_DELTA,
        FIDELITY_THRESHOLD,
        GovernanceConfig,
    )

    monkeypatch.setattr(
        tasks,
        "get_governance_config",
        lambda: GovernanceConfig(
            {
                COHERENCE_THRESHOLD: 0.7,
                CONSISTENCY_BOUND: 0.25,
                FIDELITY_THRESHOLD: 0.9,
                COUNTER_REC_DELTA: 25,
            }
        ),
    )

    with SessionLocal() as db:
        user = User(email=f"cand-{uuid.uuid4()}@example.com", role="candidate")
        db.add(user)
        db.flush()
        resume = Resume(
            user_id=user.id,
            file_id="resumes/x/y.pdf",
            file_type="pdf",
            supplementary={"extracted_text": "Shipped ML systems for 7 years."},
        )
        position = Position(title="Senior ML Engineer", description="Requires MSc CS, 8+ years.")
        db.add_all([resume, position])
        db.flush()
        assessment = Assessment(
            resume_id=resume.id, position_id=position.id, user_id=user.id
        )
        db.add(assessment)
        db.commit()
        aid = assessment.id

    result = tasks.run_assessment.apply(args=[str(aid)]).get()
    assert result["status"] == "completed"

    with SessionLocal() as db:
        stored = db.get(Assessment, aid)
        assert stored.status is AssessmentStatus.completed
        assert stored.capability_score == 81
        # traditional + semantic are deterministic keyword/embedding scores
        assert 0 <= stored.traditional_score <= 100
        assert stored.semantic_score is not None
        assert stored.score_delta == stored.capability_score - stored.traditional_score
        assert stored.governance_coherence["passed"] is True
        # audit trail persisted
        from sqlalchemy import select

        events = db.scalars(
            select(AuditTrail.event_type).where(AuditTrail.assessment_id == aid)
        ).all()
        assert "pipeline.completed" in events
        # ORM read transparently decrypts the resume supplementary back to a dict.
        resume_row = db.scalars(select(Resume).limit(1)).one()
        assert resume_row.supplementary["extracted_text"].startswith("Shipped ML")

    # Encryption-at-rest: the RAW column values must be ciphertext, not plaintext —
    # including the candidate-derived assessment JSONB (A4 follow-up).
    from sqlalchemy import text

    with engine.connect() as conn:
        raw = conn.execute(text("SELECT supplementary FROM resumes LIMIT 1")).scalar_one()
        assert raw.startswith("enc:v1:")
        assert "Shipped ML" not in raw
        gov = conn.execute(
            text("SELECT governance_coherence FROM assessments WHERE id = :id"),
            {"id": str(aid)},
        ).scalar_one()
        assert gov.startswith("enc:v1:")  # governance result encrypted at rest

    # Right to erasure (PDPA/GDPR): deleting the user cascades to resumes +
    # assessments via DB FK constraints. (The API endpoint also writes a tombstone.)
    with SessionLocal() as db:
        user = db.scalars(select(User)).first()
        db.delete(user)
        db.commit()

    with SessionLocal() as db:
        assert db.scalars(select(Assessment)).first() is None  # cascaded
        assert db.scalars(select(Resume)).first() is None  # cascaded

    Base.metadata.drop_all(engine)
    crypto._dek.cache_clear()
    crypto._index_key.cache_clear()
