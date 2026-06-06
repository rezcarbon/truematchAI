"""Notification models for in-app and email notifications."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, String, ForeignKey, JSON, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NotificationType(str, Enum):
    """Notification type enumeration."""
    interview_scheduled = "interview_scheduled"
    scorecard_request = "scorecard_request"
    candidate_advanced = "candidate_advanced"
    pipeline_update = "pipeline_update"
    system_alert = "system_alert"


class Notification(Base):
    """Notification record for in-app and email delivery."""
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status tracking
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_read", "read"),
        Index("ix_notifications_delivered", "delivered"),
    )


class EmailLog(Base):
    """Track all emails sent via the email service."""
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_email: Mapped[str] = mapped_column(String(254), nullable=False)
    template_name: Mapped[str] = mapped_column(String(50), nullable=False)
    assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="sent"
    )  # "sent", "failed", "bounced"
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # "smtp", "sendgrid", "ses"
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_email_logs_recipient", "recipient_email"),
        Index("ix_email_logs_assessment_id", "assessment_id"),
        Index("ix_email_logs_sent_at", "sent_at"),
        Index("ix_email_logs_status", "status"),
        Index("ix_email_logs_template", "template_name"),
    )


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Channel preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Notification type preferences
    notification_types: Mapped[dict] = mapped_column(
        JSON,
        default={
            "interview_scheduled": True,
            "scorecard_request": True,
            "candidate_advanced": True,
            "pipeline_update": True,
            "system_alert": True,
        },
        nullable=False
    )

    # Quiet hours configuration
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # HH:MM

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_notification_preferences_user_id", "user_id"),
    )
