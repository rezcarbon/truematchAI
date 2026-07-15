"""Analysis Result Models - Phase 3.

Captures assessment response analysis, scoring, and pattern identification.
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
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models._mixins import TimestampMixin


class AnalysisStatus(str, Enum):
    """Status of response analysis."""

    pending_analysis = "pending_analysis"
    analyzing = "analyzing"
    analysis_complete = "analysis_complete"
    scoring_complete = "scoring_complete"
    error = "error"


class AnalysisResult(Base, TimestampMixin):
    """Assessment response analysis result.

    Stores:
    - Response analysis (parsing, comprehension, correctness)
    - Scoring (objective scores per question)
    - Pattern identification (strengths, gaps, red flags)
    - Confidence levels
    - Recommendations (hire, explore, concerns)
    """

    __tablename__ = "analysis_results"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False
    )
    assessment_design_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("assessment_designs.id"), nullable=False
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False
    )

    status: Mapped[AnalysisStatus] = mapped_column(
        SQLEnum(AnalysisStatus), default=AnalysisStatus.pending_analysis
    )

    # Response analysis data (JSON)
    responses_analyzed: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Individual response analysis: {question_id: {text, parsed_intent, correctness_level, comprehension_score}}",
    )

    # Scoring data (JSON)
    scoring_results: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Objective scores: {question_id: score, rubric_alignment, confidence}",
    )

    # Pattern analysis (JSON)
    pattern_analysis: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Patterns: {strengths: [], gaps: [], red_flags: [], growth_signals: []}",
    )

    # Overall metrics (JSON)
    overall_metrics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Overall: {total_score, normalized_score (0-100), response_quality, completeness}",
    )

    # Fairness check on analysis
    analysis_fairness_check: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Bias detection in scoring: {passed, bias_indicators, issues}",
    )

    # Recommendation (JSON)
    recommendation: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Recommendation: {decision: (advance/explore/review), confidence: 0-100, rationale}",
    )

    # Analysis confidence
    overall_confidence: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="0-100 confidence in analysis"
    )

    # Analysis note
    analysis_note: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Recruiter-visible analysis summary"
    )

    # Analysis completed at
    analysis_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When analysis pipeline completed"
    )

    # Recruiter review
    recruiter_reviewed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Recruiter has reviewed analysis"
    )
    recruiter_review_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    recruiter_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Recruiter feedback on analysis"
    )

    # Relationships
    assessment = relationship("Assessment", back_populates="analysis_result")
    assessment_design = relationship("AssessmentDesign", back_populates="analysis_results")
    candidate_matches = relationship("CandidateMatch", back_populates="analysis_result")
    candidate = relationship("User", foreign_keys=[candidate_id])
    position = relationship("Position", foreign_keys=[position_id])

    __table_args__ = (
        Index("ix_analysis_results_assessment_id", "assessment_id"),
        Index("ix_analysis_results_candidate_id", "candidate_id"),
        Index("ix_analysis_results_position_id", "position_id"),
        Index("ix_analysis_results_status", "status"),
        Index("ix_analysis_results_created_at", "created_at"),
    )


__all__ = ["AnalysisResult", "AnalysisStatus"]
