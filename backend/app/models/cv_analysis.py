"""CV analysis request and result models."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class CVAnalysisStatus(str, enum.Enum):
    """Status of a CV analysis request."""
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class SeniorityLevel(str, enum.Enum):
    """Career seniority level."""
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"


class CVAnalysisRequest(Base, TimestampMixin):
    """Request to analyze a candidate's CV against a target role."""
    __tablename__ = "cv_analysis_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_role: Mapped[str] = mapped_column(String(255), nullable=False)
    target_seniority: Mapped[SeniorityLevel] = mapped_column(
        SAEnum(SeniorityLevel, name="seniority_level"),
        nullable=False,
    )
    # JSON array of capability strings they want to build
    career_focus_areas: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[CVAnalysisStatus] = mapped_column(
        SAEnum(CVAnalysisStatus, name="cv_analysis_status"),
        default=CVAnalysisStatus.pending,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_cv_analysis_requests_user_id", "user_id"),
        Index("ix_cv_analysis_requests_status", "status"),
    )


class CVAnalysisResult(Base, TimestampMixin):
    """Results of a CV analysis."""
    __tablename__ = "cv_analysis_results"

    id: Mapped[uuid.UUID] = uuid_pk()
    cv_analysis_request_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cv_analysis_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Skill gaps analysis
    missing_capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    weakness_areas: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    strength_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Job fit analysis
    top_matching_position_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    job_fit_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    underrated_positions: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # CV improvement recommendations
    improvement_suggestions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    reworded_cv_sections: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Career insights
    trajectory_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_positioning: Mapped[str | None] = mapped_column(Text, nullable=True)
    growth_opportunities: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Governance checks (quality assurance)
    governance_coherence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    governance_consistency: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    governance_fidelity: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    governance_bias_flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    governance_passed: Mapped[bool | None] = mapped_column(default=True, nullable=True)

    __table_args__ = (
        Index("ix_cv_analysis_results_request_id", "cv_analysis_request_id"),
    )
