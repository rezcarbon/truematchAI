"""JD simulation request and result models."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class JDSimulationStatus(str, enum.Enum):
    """Status of a JD simulation request."""
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class SimulationType(str, enum.Enum):
    """Type of JD simulation to run."""
    requirement_fit = "requirement_fit"  # Analyze if requirements are realistic
    market_comparison = "market_comparison"  # Compare to market standards
    candidate_archetype = "candidate_archetype"  # Test against specific archetypes


class JDSimulationRequest(Base, TimestampMixin):
    """Request to simulate and analyze a job description."""
    __tablename__ = "jd_simulation_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Either position_id or jd_text, not both required
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=True,
    )
    # Raw JD text if not using existing position
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    simulation_type: Mapped[SimulationType] = mapped_column(
        SAEnum(SimulationType, name="simulation_type"),
        nullable=False,
    )
    # JSON with seniority_level, key_skills, years_experience
    target_candidate_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[JDSimulationStatus] = mapped_column(
        SAEnum(JDSimulationStatus, name="jd_simulation_status"),
        default=JDSimulationStatus.pending,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_jd_simulation_requests_user_id", "user_id"),
        Index("ix_jd_simulation_requests_status", "status"),
    )


class JDSimulationResult(Base, TimestampMixin):
    """Results of a JD simulation."""
    __tablename__ = "jd_simulation_results"

    id: Mapped[uuid.UUID] = uuid_pk()
    jd_simulation_request_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jd_simulation_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Capability gap analysis
    critical_capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    missing_clarity: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    capability_recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Requirement creep analysis
    requirement_difficulty_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_years_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_stack_balance: Mapped[str | None] = mapped_column(Text, nullable=True)
    creep_warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Candidate fit analysis
    fit_by_archetype: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    best_archetype_fit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    talent_pool_estimate: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JD quality & market comparison
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_positioning: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_sections: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    quality_issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Wording suggestions
    suggested_job_title_variations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    improved_role_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capability_verbiage_suggestions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    benefits_suggestions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    culture_fit_language: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_jd_simulation_results_request_id", "jd_simulation_request_id"),
    )
