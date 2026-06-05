"""Interview and scorecard models for ATS features."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, Boolean, ARRAY, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.application import Application


class PipelineStage(str, Enum):
    """Pipeline stage enumeration."""
    applied = "applied"
    phone_screen = "phone_screen"
    technical = "technical"
    onsite = "onsite"
    offer = "offer"
    hired = "hired"
    rejected = "rejected"


class InterviewStatus(str, Enum):
    """Interview status enumeration."""
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class Interview(Base):
    """Interview scheduling record."""
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interviewer_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    candidate_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meeting_platform: Mapped[str | None] = mapped_column(String(50), nullable=True)  # zoom, google_meet, teams
    status: Mapped[InterviewStatus] = mapped_column(String(50), nullable=False, default=InterviewStatus.scheduled)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application: Mapped[Application] = relationship("Application", back_populates="interviews", foreign_keys=[application_id])
    scorecards: Mapped[list[Scorecard]] = relationship("Scorecard", back_populates="interview", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_interviews_application_id", "application_id"),
        Index("ix_interviews_status", "status"),
        Index("ix_interviews_scheduled_at", "scheduled_at"),
    )


class InterviewSlot(Base):
    """Interviewer availability slots."""
    __tablename__ = "interview_slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_interview_slots_interviewer_id", "interviewer_id"),
        Index("ix_interview_slots_available", "available"),
    )


class Scorecard(Base):
    """Interview scorecard for structured feedback."""
    __tablename__ = "scorecards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    interviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    competency_scores: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {competency_name: score}
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_recommendation: Mapped[str | None] = mapped_column(String(50), nullable=True)  # strong_yes, yes, no, strong_no
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interview: Mapped[Interview] = relationship("Interview", back_populates="scorecards")

    __table_args__ = (
        Index("ix_scorecards_interview_id", "interview_id"),
        Index("ix_scorecards_interviewer_id", "interviewer_id"),
    )
