"""Candidate Match Models - Phase 4.

Captures job fit scoring, ranking, and match validation.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models._mixins import TimestampMixin


class MatchStatus(str, Enum):
    """Status of candidate match analysis."""

    pending_match = "pending_match"
    matching = "matching"
    match_complete = "match_complete"
    ranked = "ranked"
    error = "error"


class FitLevel(str, Enum):
    """Overall fit level."""

    strong_fit = "strong_fit"
    good_fit = "good_fit"
    moderate_fit = "moderate_fit"
    weak_fit = "weak_fit"
    poor_fit = "poor_fit"


class CandidateMatch(Base, TimestampMixin):
    """Candidate-to-position match score and ranking.

    Stores:
    - Skill match (technical, soft skills)
    - Experience match (years, relevance, growth)
    - Compensation fit
    - Team fit prediction
    - Overall match score
    - Rank among candidates
    - Match validation & concerns
    """

    __tablename__ = "candidate_matches"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    analysis_result_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False
    )
    position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus), default=MatchStatus.pending_match
    )

    # Skill match scoring (JSON)
    skill_match: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Skill alignment: {technical: {required: [], matched: [], gaps: []}, soft: {...}, match_score: 0-100}",
    )

    # Experience match (JSON)
    experience_match: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Experience fit: {years_required, years_candidate, relevance, growth_trajectory, match_score}",
    )

    # Team fit prediction (JSON)
    team_fit: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Team compatibility: {communication_style, collaboration_signals, leadership_fit, team_match_score}",
    )

    # Compensation analysis (JSON)
    compensation_fit: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Salary expectations: {job_salary_range, candidate_expectation, alignment, stretch_factor}",
    )

    # Overall match metrics (JSON)
    overall_match: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Overall: {total_score: 0-100, fit_level: FitLevel, recommendation}",
    )

    # Match validation (JSON)
    match_validation: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Validation gates: {passed, issues: [], risk_indicators: []}",
    )

    # Ranking (batch context)
    rank_in_batch: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Rank among candidates for this position (1-based)"
    )
    percentile: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Percentile rank (0-100)"
    )

    # Fit level classification
    fit_level: Mapped[FitLevel] = mapped_column(
        SQLEnum(FitLevel), default=FitLevel.moderate_fit
    )

    # Overall match score (0-100)
    overall_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="0-100 overall match score"
    )

    # Confidence in match
    match_confidence: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="0-100 confidence in match assessment"
    )

    # Match concerns (JSON)
    concerns: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Potential concerns: {growth_gaps: [], risk_signals: [], needs_discussion: []}",
    )

    # Opportunities (JSON)
    opportunities: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Positive signals: {growth_potential: [], unique_strengths: [], value_adds: []}",
    )

    # Match completed at
    match_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When matching pipeline completed"
    )

    # Recruiter review
    recruiter_reviewed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Recruiter has reviewed match"
    )
    recruiter_review_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    recruiter_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Recruiter feedback on match"
    )

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="candidate_matches")
    hiring_outcome = relationship("HiringOutcome", back_populates="candidate_match", uselist=False)
    position = relationship("Position", foreign_keys=[position_id])
    candidate = relationship("User", foreign_keys=[candidate_id])

    __table_args__ = (
        Index("ix_candidate_matches_analysis_result_id", "analysis_result_id"),
        Index("ix_candidate_matches_position_id", "position_id"),
        Index("ix_candidate_matches_candidate_id", "candidate_id"),
        Index("ix_candidate_matches_fit_level", "fit_level"),
        Index("ix_candidate_matches_overall_score", "overall_score"),
        Index("ix_candidate_matches_rank_in_batch", "rank_in_batch"),
    )


__all__ = ["CandidateMatch", "MatchStatus", "FitLevel"]
