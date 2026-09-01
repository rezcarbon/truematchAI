"""Transition Intelligence analysis model.

One row per transition analysis. Candidate-facing: from an evidenced capability
verdict, predict the adjacent / higher-complexity roles a candidate could move
into, the upskilling gap, and an honest timeline — grounded in evidence, never
fabricated.

PII (the result narrative, target text) is encrypted at rest via the
EncryptedJSON/EncryptedText decorators, exactly like Assessment.
"""
from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class TransitionStatus(str, enum.Enum):
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class OutcomeStatus(str, enum.Enum):
    """Did a predicted transition actually happen? (Phase 3 longitudinal tracking.)"""

    predicted = "predicted"      # the analysis surfaced it; nothing acted on yet
    pursuing = "pursuing"        # the person is actively upskilling toward it
    achieved = "achieved"        # the transition happened (moved into the role)
    not_pursued = "not_pursued"  # decided against / lapsed


class TransitionAnalysis(Base, TimestampMixin):
    __tablename__ = "transition_analyses"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[TransitionStatus] = mapped_column(
        SAEnum(TransitionStatus, name="transition_status"),
        default=TransitionStatus.pending,
        nullable=False,
    )

    # Inputs
    current_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    source_language: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # Outputs — the full transition result (readiness_summary, options, notes).
    result: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    # The capability verdict the prediction is anchored on (the constant anchor).
    capability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    provenance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    # Longitudinal tracking (Phase 3): when `track` is on, a scheduled job
    # re-runs the analysis each interval and snapshots a fresh row, so the
    # candidate's readiness/capability trajectory accumulates over time.
    track: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_review_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_transition_analyses_user_id", "user_id"),
        Index("ix_transition_analyses_status", "status"),
        Index("ix_transition_analyses_resume_id", "resume_id"),
        Index("ix_transition_analyses_review", "track", "next_review_at"),
    )


class TransitionOutcome(Base, TimestampMixin):
    """A recorded real-world outcome for a predicted transition pathway.

    Closes the loop: the platform predicted a pathway; this records whether the
    person actually pursued/achieved it. Aggregated, these measure transition
    success across a cohort (the "did workers actually move into higher-value
    roles?" mandate metric).
    """

    __tablename__ = "transition_outcomes"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("transition_analyses.id", ondelete="CASCADE"), nullable=False
    )
    predicted_role: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[OutcomeStatus] = mapped_column(
        SAEnum(OutcomeStatus, name="outcome_status"),
        default=OutcomeStatus.predicted,
        nullable=False,
    )
    actual_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    note: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    __table_args__ = (
        Index("ix_transition_outcomes_user_id", "user_id"),
        Index("ix_transition_outcomes_analysis_id", "analysis_id"),
        Index("ix_transition_outcomes_status", "status"),
    )
