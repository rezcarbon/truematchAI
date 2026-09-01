"""Governance log model — tracks gate execution in strict sequence."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class GateName(str, enum.Enum):
    """Governance gates that execute in strict sequence."""
    coherence = "coherence"
    consistency = "consistency"
    fidelity = "fidelity"
    bias_check = "bias_check"


class GovernanceLog(Base, TimestampMixin):
    """
    Immutable record of governance gate execution for an assessment.

    Each gate executes in a strict sequence per assessment_id. The
    (assessment_id, gate_sequence) pair is UNIQUE to prevent duplicate
    gates in the sequence. created_at is server-set on insertion and
    immutable thereafter.
    """
    __tablename__ = "governance_logs"

    id: Mapped[uuid.UUID] = uuid_pk()

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )

    gate_sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    gate_name: Mapped[GateName] = mapped_column(
        SAEnum(GateName, name="gate_name"),
        nullable=False,
    )

    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    observations: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "gate_sequence",
            name="uq_governance_logs_assessment_sequence",
        ),
        Index("ix_governance_logs_assessment_id", "assessment_id"),
        Index("ix_governance_logs_created_at", "created_at"),
    )
