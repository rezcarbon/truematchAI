"""Decision model — recruiter action on an assessment."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedText


class DecisionOutcome(str, enum.Enum):
    advance = "advance"
    reject = "reject"
    hold = "hold"
    interview = "interview"
    hire = "hire"


class Decision(Base, TimestampMixin):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = uuid_pk()
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision: Mapped[DecisionOutcome] = mapped_column(
        SAEnum(DecisionOutcome, name="decision_outcome"),
        nullable=False,
    )
    ai_recommendation_followed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Free-text recruiter notes — may reference candidate PII; encrypted at rest.
    override_reasoning: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    cultural_fit_notes: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    interview_notes: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    __table_args__ = (
        Index("ix_decisions_assessment_id", "assessment_id"),
        Index("ix_decisions_position_id", "position_id"),
    )
