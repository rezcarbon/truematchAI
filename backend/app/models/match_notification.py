"""Match Notification Timeline - Quick Win Feature.

Tracks candidate profile status updates in the matching process.
Enables transparent notifications: "Profile sent 2h ago → Viewed 1h ago → Interview scheduled".
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models._mixins import TimestampMixin


class NotificationStatus(str, Enum):
    """Status of match in the pipeline."""

    profile_sent = "profile_sent"  # Candidate profile sent to recruiter
    profile_viewed = "profile_viewed"  # Recruiter viewed profile
    interview_scheduled = "interview_scheduled"  # Interview scheduled
    interview_completed = "interview_completed"  # Interview happened
    offer_received = "offer_received"  # Offer extended
    rejected = "rejected"  # Candidate rejected or position filled


class MatchNotification(Base, TimestampMixin):
    """Timeline of match status updates for candidate visibility.

    Stores:
    - When profile was sent
    - When recruiter viewed it
    - When interview was scheduled/completed
    - When offer was extended
    - Status messages for transparency
    """

    __tablename__ = "match_notifications"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    candidate_match_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidate_matches.id"), nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus), nullable=False
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Human-readable status message"
    )
    status_timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="When this status occurred"
    )

    # Email notification sent
    email_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether email notification was sent"
    )
    email_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Relationships
    candidate_match = relationship("CandidateMatch", back_populates="notifications")

    __table_args__ = (
        Index("ix_match_notifications_candidate_match_id", "candidate_match_id"),
        Index("ix_match_notifications_status", "status"),
        Index("ix_match_notifications_timestamp", "status_timestamp"),
    )


__all__ = ["MatchNotification", "NotificationStatus"]
