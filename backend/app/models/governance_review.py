"""Governance review model for failed checks requiring human review."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class ReviewType(str, enum.Enum):
    """Type of governance review required."""
    cv_analysis = "cv_analysis"
    assessment = "assessment"
    jd_simulation = "jd_simulation"


class ReviewStatus(str, enum.Enum):
    """Status of governance review."""
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"


class GovernanceReview(Base, TimestampMixin):
    """Record of governance gate failure requiring human review."""
    __tablename__ = "governance_reviews"

    id: Mapped[uuid.UUID] = uuid_pk()

    # What failed
    review_type: Mapped[ReviewType] = mapped_column(
        SAEnum(ReviewType, name="review_type"),
        nullable=False,
    )

    # Reference to the resource being reviewed
    resource_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Which gates failed
    failed_gates: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    gate_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Summary of failure
    failure_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Review decision
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, name="review_status"),
        default=ReviewStatus.pending,
        nullable=False,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_governance_reviews_status", "status"),
        Index("ix_governance_reviews_user_id", "user_id"),
        Index("ix_governance_reviews_reviewed_by", "reviewed_by"),
        Index("ix_governance_reviews_resource_id", "resource_id"),
        Index("ix_governance_reviews_review_type", "review_type"),
    )
