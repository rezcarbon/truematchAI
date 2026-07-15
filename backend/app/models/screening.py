"""Screening models — agent-generated candidate evaluations."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class ScreeningRecommendation(str, enum.Enum):
    """Agent screening recommendation types.

    CRITICAL: Agent can only recommend, never exclude.
    Only output: advance (interview), hold (queue), review (escalate to human)
    """
    advance = "advance"  # Clear fit, recommend interview
    hold = "hold"  # Potential fit, needs recruiter review
    review = "review"  # Unclear or governance concern, escalate to human
    # NOTE: No "reject" or "exclude" option - recruiter only decides exclusion


class ScreeningBatchStatus(str, enum.Enum):
    """Batch processing status."""
    queued = "queued"  # Waiting to start screening
    screening = "screening"  # Actively screening candidates
    pending_review = "pending_review"  # All screened, awaiting recruiter review
    completed = "completed"  # All recruiter decisions recorded


class RecruiterDecision(str, enum.Enum):
    """Recruiter decision on screened candidate."""
    interview = "interview"  # Proceed to interview
    hold = "hold"  # Hold for later consideration
    further_review = "further_review"  # Request additional analysis
    # NOTE: Reject decision is made outside screening phase


class ScreeningBatch(Base, TimestampMixin):
    """Batch of candidates being screened for a position."""
    __tablename__ = "screening_batches"

    id: Mapped[uuid.UUID] = uuid_pk()
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Batch tracking
    status: Mapped[ScreeningBatchStatus] = mapped_column(
        SAEnum(ScreeningBatchStatus, name="screening_batch_status"),
        default=ScreeningBatchStatus.queued,
        nullable=False,
    )
    total_candidates: Mapped[int] = mapped_column(Integer, nullable=False)
    screened_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Batch configuration (encrypted for sensitivity)
    batch_config: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    # Example: {
    #   "min_experience_years": 3,
    #   "required_skills": ["Python", "React"],
    #   "red_flag_keywords": ["unreliable", "toxic"],
    #   "custom_criteria": {...}
    # }

    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_screening_batches_position_id_status", position_id, status),
        Index("ix_screening_batches_created_by", created_by),
        Index("ix_screening_batches_created_at", "created_at"),
    )


class ScreeningResult(Base, TimestampMixin):
    """Result of screening a single resume against a position."""
    __tablename__ = "screening_results"

    id: Mapped[uuid.UUID] = uuid_pk()
    screening_batch_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Agent screening recommendation
    agent_recommendation: Mapped[ScreeningRecommendation] = mapped_column(
        SAEnum(ScreeningRecommendation, name="screening_recommendation"),
        nullable=False,
    )
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100

    # Recruiter-facing summary (encrypted)
    screening_summary: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    # Example: "RECOMMENDATION: ADVANCE (confidence: 85%)\n\n
    #  CANDIDATE SNAPSHOT:\n...
    #  KEY MATCHES:\n...
    #  SKILLS GAPS:\n...
    #  etc."

    # Full screening analysis (encrypted)
    screening_details: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    # Contains:
    # {
    #   "skills_matched": [...],
    #   "skills_missing": [...],
    #   "experience_fit": {...},
    #   "career_trajectory": {...},
    #   "red_flags": [...],
    #   "learning_signals": {...}
    # }

    # Conscience checks (encrypted for sensitivity)
    bias_flags: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False, default={})
    # Contains:
    # {
    #   "demographic_indicators": [...],
    #   "potential_disparate_impact": bool,
    #   "fairness_notes": str,
    #   "should_be_reviewed": bool,
    #   "governance_escalation": bool
    # }

    # Recruiter decision
    recruiter_decision: Mapped[RecruiterDecision | None] = mapped_column(
        SAEnum(RecruiterDecision, name="recruiter_decision"),
        nullable=True,
    )
    recruiter_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    recruiter_notes: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    recruiter_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100

    # Override tracking (for learning)
    was_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # True if recruiter_decision != agent_recommendation
    override_reason: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    __table_args__ = (
        Index("ix_screening_results_batch_id", screening_batch_id),
        Index("ix_screening_results_position_id", position_id),
        Index("ix_screening_results_resume_id", resume_id),
        Index("ix_screening_results_recruiter_id", recruiter_id),
        Index("ix_screening_results_position_recruiter_decision", position_id, recruiter_decision),
        Index("ix_screening_results_created_at", "created_at"),
        Index("ix_screening_results_batch_decision", screening_batch_id, recruiter_decision),
    )


__all__ = [
    "ScreeningBatch",
    "ScreeningResult",
    "ScreeningRecommendation",
    "ScreeningBatchStatus",
    "RecruiterDecision",
]
