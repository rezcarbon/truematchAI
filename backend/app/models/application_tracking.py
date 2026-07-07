"""Application tracking models for detailed funnel analytics and engagement metrics."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.database import Base
from app.models._types import EncryptedText


class ApplicationEventType(str, enum.Enum):
    """Types of events that can occur on an application."""
    status_changed = "status_changed"
    message_sent = "message_sent"
    message_received = "message_received"
    viewed = "viewed"
    interview_scheduled = "interview_scheduled"
    interview_completed = "interview_completed"
    offer_extended = "offer_extended"
    offer_accepted = "offer_accepted"
    offer_rejected = "offer_rejected"
    rejected = "rejected"
    withdrawn = "withdrawn"
    feedback_provided = "feedback_provided"
    reassigned = "reassigned"
    flagged = "flagged"
    unflagged = "unflagged"


class ActorType(str, enum.Enum):
    """Type of actor triggering an event."""
    system = "system"
    user = "user"
    automation = "automation"
    ats_sync = "ats_sync"


class ApplicationEvent(Base):
    """
    Detailed activity log for applications.

    Tracks all events throughout the application lifecycle:
    - Status changes
    - Messages and communications
    - Interview scheduling
    - Feedback submissions
    - Administrative actions
    """
    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Event details
    event_type: Mapped[ApplicationEventType] = mapped_column(String(100), nullable=False)
    event_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Actor tracking (who triggered the event)
    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_type: Mapped[ActorType] = mapped_column(String(50), nullable=False, default=ActorType.system)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index("ix_application_events_application_id", "application_id"),
        Index("ix_application_events_user_id", "user_id"),
        Index("ix_application_events_event_type", "event_type"),
        Index("ix_application_events_created_at", "created_at"),
        Index("ix_application_events_triggered_by_id", "triggered_by_id"),
        Index("ix_application_events_app_type", "application_id", "event_type"),
        Index("ix_application_events_app_created", "application_id", "created_at"),
    )


class FeedbackRecommendation(str, enum.Enum):
    """Recommendation from feedback provider."""
    proceed = "proceed"
    maybe = "maybe"
    reject = "reject"


class ApplicationFeedback(Base):
    """
    Structured feedback collected during application interviews/assessments.

    Stores feedback from interviewers and evaluators:
    - Interview scorecards
    - Assessment results
    - Stage-specific evaluations
    - Decision recommendations
    """
    __tablename__ = "application_feedback"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    feedback_stage: Mapped[str] = mapped_column(String(50), nullable=False)  # phone_screen, technical, onsite, etc.

    # Feedback content - PII should be encrypted
    overall_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 scale
    feedback_text: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    structured_feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Interviewer/reviewer info
    provided_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provided_by_name: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Decision tracking
    recommendation: Mapped[FeedbackRecommendation | None] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_application_feedback_application_id", "application_id"),
        Index("ix_application_feedback_stage", "feedback_stage"),
        Index("ix_application_feedback_provided_by_id", "provided_by_id"),
        Index("ix_application_feedback_recommendation", "recommendation"),
        Index("ix_application_feedback_created_at", "created_at"),
        Index("ix_application_feedback_app_stage", "application_id", "feedback_stage"),
    )
