"""Application timeline model for tracking assessment events and milestones."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class EventType(str, enum.Enum):
    """Timeline event types."""
    status_change = "status_change"
    feedback_shared = "feedback_shared"
    interview_scheduled = "interview_scheduled"
    offer_extended = "offer_extended"
    offer_accepted = "offer_accepted"
    interview_completed = "interview_completed"
    application_rejected = "application_rejected"
    assessment_completed = "assessment_completed"


class ApplicationTimeline(Base, TimestampMixin):
    """
    Application timeline tracking events and milestones.

    Maintains chronological record of:
    - Status transitions through the hiring pipeline
    - Interview scheduling and completion
    - Feedback sharing events
    - Offer events (extended, accepted, rejected)
    - Assessment completion events
    """
    __tablename__ = "application_timelines"

    id: Mapped[uuid.UUID] = uuid_pk()
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Timeline events array: list of timestamped events with metadata
    events: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Individual event tracking for performance
    latest_event_type: Mapped[EventType | None] = mapped_column(
        String(50),
        nullable=True,
    )
    latest_event_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    latest_event_data: Mapped[dict | None] = mapped_column(
        EncryptedJSON,
        nullable=True,
    )

    # Summary of major milestones
    status_change_count: Mapped[int] = mapped_column(default=0, nullable=False)
    feedback_events_count: Mapped[int] = mapped_column(default=0, nullable=False)
    interview_events_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Tracking completion
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_application_timelines_assessment_id", "assessment_id"),
        Index("ix_application_timelines_application_id", "application_id"),
        Index("ix_application_timelines_latest_event_type", "latest_event_type"),
        Index("ix_application_timelines_latest_event_timestamp", "latest_event_timestamp"),
        Index("ix_application_timelines_is_active", "is_active"),
        Index(
            "ix_application_timelines_assessment_timestamp",
            "assessment_id",
            "latest_event_timestamp",
        ),
    )
