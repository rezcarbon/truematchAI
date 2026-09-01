"""Disparate impact analysis model — bias monitoring and detection."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class DisparateImpactAnalysis(Base, TimestampMixin):
    """
    Disparate impact analysis for a position over a time period.

    Tracks selection rates by demographic group and reference group,
    calculates the four-fifths ratio (80% rule), and flags instances
    where the ratio falls below 0.8 threshold (indicating potential
    disparate impact under Title VII).

    analysis_details stores raw computation data (sample sizes, counts,
    rates) for audit and reproducibility.
    """
    __tablename__ = "disparate_impact_analyses"

    id: Mapped[uuid.UUID] = uuid_pk()

    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Analysis period as a string, e.g., "2026-06-01 to 2026-06-30"
    analysis_period: Mapped[str] = mapped_column(String(255), nullable=False)

    # Demographic group being analyzed (e.g., "women", "minorities", "age_50+")
    demographic_group: Mapped[str] = mapped_column(String(128), nullable=False)

    # Number of candidates in this demographic group who applied
    population_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Selection rate for this group (0-1, e.g., 0.60 = 60% selected)
    selection_rate: Mapped[float] = mapped_column(Float, nullable=False)

    # Reference group for comparison (e.g., "men", "majority", "age_under_50")
    reference_group: Mapped[str] = mapped_column(String(128), nullable=False)

    # Selection rate for the reference group (0-1)
    reference_selection_rate: Mapped[float] = mapped_column(Float, nullable=False)

    # Four-fifths ratio: selection_rate / reference_selection_rate
    # Disparate impact flagged when < 0.8 (80% rule under Title VII)
    four_fifths_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    # True if four_fifths_ratio < 0.8 (disparate impact detected)
    is_disparate_impact: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Raw analysis data: sample counts, thresholds, rounding notes, etc.
    # Useful for audit trails and reproducibility of calculations.
    analysis_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_disparate_impact_analyses_position_id", "position_id"),
        Index("ix_disparate_impact_analyses_created_at", "created_at"),
    )


class DisparateImpactFlag(Base, TimestampMixin):
    """
    Governance gate output: flag triggered when disparate impact detected.

    Records the reasoning, affected group, and recommended action for human
    review. Used to escalate hiring decisions that fail the disparate impact
    gate to human review rather than allowing automated progression.
    """
    __tablename__ = "disparate_impact_flags"

    id: Mapped[uuid.UUID] = uuid_pk()

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # True if disparate impact was detected (ratio < 0.8)
    flag_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Human-readable explanation, e.g.:
    # "Women's selection rate 60% vs men's 85% = 0.71 ratio < 0.8"
    reason: Mapped[str] = mapped_column(String, nullable=False)

    # The demographic group affected by the disparate impact
    affected_group: Mapped[str] = mapped_column(String(128), nullable=False)

    # Recommended action for governance gate handler, e.g.:
    # "escalate to human review", "pause hiring", "retrain model"
    recommended_action: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        Index("ix_disparate_impact_flags_assessment_id", "assessment_id"),
        Index("ix_disparate_impact_flags_created_at", "created_at"),
    )
