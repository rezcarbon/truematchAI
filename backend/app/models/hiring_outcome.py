"""Hiring Outcome Models - Phase 5.

Captures hiring outcomes, learning feedback, and continuous improvement.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models._mixins import TimestampMixin


class HiringDecision(str, Enum):
    """Final hiring outcome."""

    hired = "hired"
    not_hired = "not_hired"
    offer_declined = "offer_declined"
    withdrawn = "withdrawn"
    pending = "pending"


class PerformanceRating(str, Enum):
    """Post-hire performance rating."""

    exceeding = "exceeding"
    meeting = "meeting"
    developing = "developing"
    underperforming = "underperforming"


class HiringOutcome(Base, TimestampMixin):
    """Hiring outcome tracking for learning and evolution.

    Stores:
    - Hiring decision (hired/not hired/offer declined)
    - Hire date and tenure
    - Post-hire performance rating
    - Retention signal
    - Learning feedback for agent improvement
    - Prediction accuracy tracking
    """

    __tablename__ = "hiring_outcomes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    candidate_match_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidate_matches.id"), nullable=False
    )
    position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Hiring decision
    hiring_decision: Mapped[HiringDecision] = mapped_column(
        SQLEnum(HiringDecision), default=HiringDecision.pending
    )
    decision_made_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When hiring decision was made"
    )
    decision_rationale: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Reason for decision"
    )

    # Hire information (if hired)
    hired: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether candidate was hired"
    )
    hire_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Start date if hired"
    )
    tenure_days: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Days employed if hired"
    )

    # Post-hire performance (if hired and enough time passed)
    performance_rating: Mapped[PerformanceRating | None] = mapped_column(
        SQLEnum(PerformanceRating), nullable=True, comment="Performance rating after 90+ days"
    )
    performance_evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When performance was evaluated"
    )
    performance_details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Performance context: {on_time: bool, quality: score, feedback: text}",
    )

    # Retention signal
    retained: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="Still employed (if hired)"
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Last known active date"
    )

    # Agent prediction accuracy tracking
    screening_recommendation: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="What screening agent recommended (advance/hold/review)",
    )
    assessment_recommendation: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="What assessment agent recommended",
    )
    match_score_at_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="What matching agent scored (0-100)"
    )
    actual_performance_vs_prediction: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Accuracy: {prediction_correct: bool, variance: score_diff, factors: []}",
    )

    # Learning feedback (JSON)
    learning_feedback: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Feedback for evolution agent: {assessment_predictiveness, interview_signals, skill_match_accuracy}",
    )

    # Bias detection feedback
    bias_signals: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Did assessment process show any bias: {suspected_bias: [], protected_attributes: []}",
    )

    # Improvement opportunities
    improvement_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="What could be improved for future hires"
    )

    # Recruiter feedback on outcome
    recruiter_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Recruiter feedback on hiring outcome"
    )

    # Relationships
    candidate_match = relationship("CandidateMatch", back_populates="hiring_outcome")
    position = relationship("Position", foreign_keys=[position_id])
    candidate = relationship("User", foreign_keys=[candidate_id])

    __table_args__ = (
        Index("ix_hiring_outcomes_candidate_match_id", "candidate_match_id"),
        Index("ix_hiring_outcomes_position_id", "position_id"),
        Index("ix_hiring_outcomes_candidate_id", "candidate_id"),
        Index("ix_hiring_outcomes_hiring_decision", "hiring_decision"),
        Index("ix_hiring_outcomes_performance_rating", "performance_rating"),
        Index("ix_hiring_outcomes_hire_date", "hire_date"),
    )


__all__ = ["HiringOutcome", "HiringDecision", "PerformanceRating"]
