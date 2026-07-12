"""Job application models for tracking candidate applications through the hiring pipeline."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class ApplicationStatus(str, enum.Enum):
    """Status of a job application."""
    submitted = "submitted"
    acknowledged = "acknowledged"
    screening = "screening"
    interview_scheduled = "interview_scheduled"
    interview_completed = "interview_completed"
    offer_extended = "offer_extended"
    offer_accepted = "offer_accepted"
    offer_rejected = "offer_rejected"
    rejected = "rejected"
    withdrawn = "withdrawn"
    archived = "archived"


class ApplicationEventType(str, enum.Enum):
    """Types of events that can occur during an application lifecycle."""
    submitted = "submitted"
    acknowledged = "acknowledged"
    status_changed = "status_changed"
    interview_scheduled = "interview_scheduled"
    interview_completed = "interview_completed"
    feedback_provided = "feedback_provided"
    offer_extended = "offer_extended"
    offer_accepted = "offer_accepted"
    offer_rejected = "offer_rejected"
    rejected = "rejected"
    withdrawn = "withdrawn"
    message_sent = "message_sent"
    message_received = "message_received"
    reassigned = "reassigned"
    flagged = "flagged"
    unflagged = "unflagged"


class JobApplication(Base, TimestampMixin):
    """
    Job application record tracking candidate progress through hiring pipeline.

    Tracks a candidate's application to a specific position, including:
    - Current status through the pipeline
    - Resume used for application
    - Cover note and submission details
    - Audit trail of status changes and events

    Attributes:
        id: Unique identifier for this application
        user_id: Foreign key to the candidate user
        position_id: Foreign key to the job position
        resume_id: Foreign key to the resume used in application
        status: Current ApplicationStatus
        cover_note: Candidate's cover letter/note (encrypted at rest)
        source: How application was submitted (linkedin, referral, etc.)
        external_ref: Reference to external ATS system for idempotent imports
        tags: Custom tags for categorizing applications
        applied_at: When application was submitted
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
        archived_at: Soft delete timestamp
    """
    __tablename__ = "job_applications"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Application tracking
    status: Mapped[ApplicationStatus] = mapped_column(
        String(50),
        nullable=False,
        default=ApplicationStatus.submitted,
    )

    # Candidate communication
    cover_note: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)

    # Submission metadata
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    external_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships (lazy import to avoid circular dependency)
    user: Mapped[list] = relationship("User", lazy="select", foreign_keys=[user_id])
    position: Mapped[list] = relationship("Position", lazy="select", foreign_keys=[position_id])
    resume: Mapped[list] = relationship("Resume", lazy="select", foreign_keys=[resume_id])
    timeline_events: Mapped[list[ApplicationTimeline]] = relationship(
        "ApplicationTimeline",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_job_applications_user_id", "user_id"),
        Index("ix_job_applications_position_id", "position_id"),
        Index("ix_job_applications_resume_id", "resume_id"),
        Index("ix_job_applications_status", "status"),
        Index("ix_job_applications_applied_at", "applied_at"),
        Index("ix_job_applications_external_ref", "external_ref"),
        Index("ix_job_applications_user_position", "user_id", "position_id"),
        Index("ix_job_applications_user_status", "user_id", "status"),
        Index("ix_job_applications_archived_at", "archived_at"),
    )

    def __repr__(self) -> str:
        """Concise repr for debugging."""
        return (
            f"<JobApplication id={self.id!r} user_id={self.user_id!r} "
            f"position_id={self.position_id!r} status={self.status.value}>"
        )

    def update_status(
        self,
        new_status: ApplicationStatus,
        session,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ApplicationTimeline:
        """
        Update application status and create timeline event.

        Atomically updates the application status and logs the transition as
        an ApplicationTimeline event for audit trail.

        Args:
            new_status: Target ApplicationStatus
            session: SQLAlchemy session
            reason: Optional reason for status change
            metadata: Optional metadata about the change

        Returns:
            ApplicationTimeline event created for this status change

        Example:
            >>> event = app.update_status(
            ...     ApplicationStatus.interview_scheduled,
            ...     session,
            ...     reason="Interview confirmed",
            ...     metadata={"interview_date": "2025-08-15"}
            ... )
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = utcnow()

        # Create timeline event
        event = ApplicationTimeline(
            application_id=self.id,
            event_type=ApplicationEventType.status_changed,
            event_data={
                "previous_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason,
                **(metadata or {}),
            },
        )

        session.add(event)
        session.commit()
        return event

    def add_event(
        self,
        session,
        event_type: ApplicationEventType,
        event_data: Optional[dict] = None,
        description: Optional[str] = None,
    ) -> ApplicationTimeline:
        """
        Add an event to the application timeline.

        Creates a new ApplicationTimeline record for any event that occurs
        during the application lifecycle.

        Args:
            session: SQLAlchemy session
            event_type: Type of event
            event_data: Optional structured data about the event
            description: Optional human-readable description

        Returns:
            ApplicationTimeline event created

        Example:
            >>> event = app.add_event(
            ...     session,
            ...     ApplicationEventType.interview_scheduled,
            ...     event_data={"date": "2025-08-15", "time": "14:00"},
            ...     description="Phone screen with Sarah"
            ... )
        """
        event = ApplicationTimeline(
            application_id=self.id,
            event_type=event_type,
            event_data=event_data,
            description=description,
        )

        session.add(event)
        session.commit()
        return event

    def get_timeline(self, session, limit: Optional[int] = None) -> list[ApplicationTimeline]:
        """
        Retrieve the timeline of events for this application.

        Returns all ApplicationTimeline events for this application,
        ordered chronologically from earliest to latest.

        Args:
            session: SQLAlchemy session
            limit: Max results to return (optional)

        Returns:
            List of ApplicationTimeline events

        Example:
            >>> timeline = app.get_timeline(session)
            >>> for event in timeline:
            ...     print(f"{event.created_at}: {event.event_type.value}")
        """
        query = session.query(ApplicationTimeline).filter(
            ApplicationTimeline.application_id == self.id,
        ).order_by(ApplicationTimeline.created_at.asc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def validate_status_transition(self, new_status: ApplicationStatus) -> tuple[bool, Optional[str]]:
        """
        Validate if a status transition is allowed.

        Implements business logic for valid state transitions.
        For example, can't go from rejected back to submitted.

        Args:
            new_status: Target status

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> is_valid, error = app.validate_status_transition(ApplicationStatus.rejected)
            >>> if not is_valid:
            ...     print(f"Cannot transition: {error}")
        """
        current = self.status
        reason = None

        # Can't transition from terminal states
        if current == ApplicationStatus.rejected:
            return False, "Cannot transition from rejected status"
        if current == ApplicationStatus.offer_accepted:
            return False, "Cannot transition from accepted offer"
        if current == ApplicationStatus.archived:
            return False, "Cannot transition from archived status"

        # Can't go backwards
        status_order = [
            ApplicationStatus.submitted,
            ApplicationStatus.acknowledged,
            ApplicationStatus.screening,
            ApplicationStatus.interview_scheduled,
            ApplicationStatus.interview_completed,
            ApplicationStatus.offer_extended,
        ]

        if current in status_order and new_status in status_order:
            if status_order.index(new_status) < status_order.index(current):
                return False, f"Cannot transition backward from {current.value} to {new_status.value}"

        return True, None

    def to_dict(self) -> dict:
        """
        Export to dictionary (excluding encrypted fields).

        Returns:
            Dict with non-sensitive application data

        Example:
            >>> app_dict = app.to_dict()
            >>> print(f"Status: {app_dict['status']}")
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "position_id": str(self.position_id),
            "resume_id": str(self.resume_id),
            "status": self.status.value if isinstance(self.status, ApplicationStatus) else self.status,
            "source": self.source,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
