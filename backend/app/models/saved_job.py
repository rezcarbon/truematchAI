"""Saved jobs model for candidate job curation and tracking."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Integer, Float, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.database import Base
from app.models._types import EncryptedJSON, EncryptedText


class SavedJobStatus(str, enum.Enum):
    """Status of a saved job."""
    saved = "saved"
    viewed = "viewed"
    applied = "applied"
    archived = "archived"
    rejected = "rejected"


class SavedJob(Base):
    """
    Saved jobs for candidate job curation.

    Allows candidates to:
    - Save jobs they're interested in
    - Organize saves into custom lists
    - Track application history
    - Receive updates on saved jobs
    - Store personalized notes and relevance scores

    Attributes:
        id: Unique identifier
        user_id: Foreign key to the candidate user
        position_id: Foreign key to the job position
        list_id: Foreign key to SavedJobsList (optional)
        list_name: Name of the list (for quick filtering)
        notes: User's personal notes about this job
        job_title: Denormalized job title from position
        company_name: Denormalized company name
        job_url: URL to the job posting
        match_score: Relevance score (0-100)
        relevance_metadata: ML-generated match metadata (encrypted)
        status: Current status of this saved job
        viewed_at: When user viewed this job
        applied_at: When user applied to this job
        notify_on_update: Whether to notify on job updates
        last_notified_at: Last notification timestamp
        created_at: When this was saved
        updated_at: Last modification timestamp
        archived_at: Soft delete timestamp
    """
    __tablename__ = "saved_jobs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    list_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("saved_jobs_lists.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Save metadata
    list_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Default")
    notes: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)

    # Job snapshot (denormalized for fast access without joins)
    job_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    job_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Relevance and matching scores (encrypted - PII)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relevance_metadata: Mapped[Optional[dict]] = mapped_column(EncryptedJSON, nullable=True)

    # Status tracking
    status: Mapped[SavedJobStatus] = mapped_column(String(50), nullable=False, default=SavedJobStatus.saved)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Notification preferences
    notify_on_update: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships (lazy import to avoid circular dependency)
    user: Mapped[list] = relationship("User", lazy="select", foreign_keys=[user_id])
    position: Mapped[list] = relationship("Position", lazy="select", foreign_keys=[position_id])
    job_list: Mapped[list] = relationship("SavedJobsList", lazy="select", foreign_keys=[list_id])

    __table_args__ = (
        UniqueConstraint("user_id", "position_id", name="uq_saved_jobs_user_position"),
        Index("ix_saved_jobs_user_id", "user_id"),
        Index("ix_saved_jobs_position_id", "position_id"),
        Index("ix_saved_jobs_status", "status"),
        Index("ix_saved_jobs_list_name", "list_name"),
        Index("ix_saved_jobs_list_id", "list_id"),
        Index("ix_saved_jobs_created_at", "created_at"),
        Index("ix_saved_jobs_archived_at", "archived_at"),
        Index("ix_saved_jobs_user_status", "user_id", "status"),
        Index("ix_saved_jobs_user_created", "user_id", "created_at"),
        Index("ix_saved_jobs_user_list_status", "user_id", "list_name", "status"),
    )

    def __repr__(self) -> str:
        """Concise repr for debugging."""
        return (
            f"<SavedJob id={self.id!r} user_id={self.user_id!r} "
            f"position_id={self.position_id!r} status={self.status.value}>"
        )

    def toggle_save(self, session) -> bool:
        """
        Toggle the saved status of this job.

        If saved -> archived, if archived -> saved. Updates status and timestamps.
        Returns the new state (True if now saved, False if now archived).

        Args:
            session: SQLAlchemy session for persistence

        Returns:
            bool: True if now saved, False if now archived

        Example:
            >>> is_saved = job.toggle_save(session)
            >>> print(f"Job is now {'saved' if is_saved else 'archived'}")
        """
        now = utcnow()
        old_status = self.status

        if self.status == SavedJobStatus.saved:
            self.status = SavedJobStatus.archived
            self.archived_at = now
            result = False
        elif self.status == SavedJobStatus.archived:
            self.status = SavedJobStatus.saved
            self.archived_at = None
            result = True
        else:
            # For other statuses (viewed, applied, rejected), save it
            self.status = SavedJobStatus.saved
            self.archived_at = None
            result = True

        self.updated_at = now
        session.commit()
        return result

    def update_status(self, new_status: SavedJobStatus, session) -> SavedJob:
        """
        Update the status of this saved job.

        Updates timestamps based on new status:
        - viewed: sets viewed_at
        - applied: sets applied_at
        - archived: sets archived_at

        Args:
            new_status: New SavedJobStatus
            session: SQLAlchemy session for persistence

        Returns:
            self for chaining

        Example:
            >>> job.update_status(SavedJobStatus.viewed, session)
            >>> job.update_status(SavedJobStatus.applied, session)
        """
        now = utcnow()
        self.status = new_status
        self.updated_at = now

        if new_status == SavedJobStatus.viewed:
            if not self.viewed_at:
                self.viewed_at = now
        elif new_status == SavedJobStatus.applied:
            if not self.applied_at:
                self.applied_at = now
        elif new_status == SavedJobStatus.archived:
            if not self.archived_at:
                self.archived_at = now

        session.commit()
        return self

    @classmethod
    def get_user_saved_jobs(
        cls,
        session,
        user_id: uuid.UUID,
        status: Optional[SavedJobStatus] = None,
        list_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SavedJob]:
        """
        Retrieve saved jobs for a specific user.

        Supports filtering by status and/or list name. Respects soft deletes
        (archived_at=None when not explicitly filtering for archived).

        Args:
            session: SQLAlchemy session
            user_id: Target user ID
            status: Filter by SavedJobStatus (optional)
            list_name: Filter by list name (optional)
            limit: Max results to return (default 100)
            offset: For pagination (default 0)

        Returns:
            List of SavedJob records

        Example:
            >>> saved = SavedJob.get_user_saved_jobs(session, user_id)
            >>> saved = SavedJob.get_user_saved_jobs(
            ...     session, user_id, status=SavedJobStatus.saved
            ... )
            >>> saved = SavedJob.get_user_saved_jobs(
            ...     session, user_id, list_name="Dream Jobs"
            ... )
        """
        query = session.query(cls).filter(cls.user_id == user_id)

        if status:
            query = query.filter(cls.status == status)
        else:
            # By default exclude archived unless explicitly requested
            query = query.filter(cls.status != SavedJobStatus.archived)

        if list_name:
            query = query.filter(cls.list_name == list_name)

        return query.order_by(cls.created_at.desc()).limit(limit).offset(offset).all()

    @classmethod
    def get_user_saved_count(
        cls,
        session,
        user_id: uuid.UUID,
        status: Optional[SavedJobStatus] = None,
    ) -> int:
        """
        Get count of saved jobs for a user.

        Args:
            session: SQLAlchemy session
            user_id: Target user ID
            status: Filter by status (optional)

        Returns:
            Count of saved jobs

        Example:
            >>> count = SavedJob.get_user_saved_count(session, user_id)
            >>> print(f"User has {count} saved jobs")
        """
        query = session.query(cls).filter(cls.user_id == user_id)

        if status:
            query = query.filter(cls.status == status)

        return query.count()

    def to_dict(self) -> dict:
        """
        Export to dictionary (excluding encrypted fields).

        Returns:
            Dict with non-sensitive metadata

        Example:
            >>> data = job.to_dict()
            >>> print(f"Match score: {data['match_score']}")
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "position_id": str(self.position_id),
            "list_id": str(self.list_id) if self.list_id else None,
            "list_name": self.list_name,
            "notes": self.notes,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "job_url": self.job_url,
            "match_score": self.match_score,
            "status": self.status.value if isinstance(self.status, SavedJobStatus) else self.status,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "notify_on_update": self.notify_on_update,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }


class SavedJobsList(Base):
    """
    Custom lists for organizing saved jobs.

    Allows candidates to organize jobs into custom folders/lists:
    - Default list for general saves
    - Custom lists like "Dream Jobs", "Startups", "Remote Only", etc.
    - Shared lists for collaboration

    Attributes:
        id: Unique identifier
        user_id: Foreign key to the owner user
        name: Display name for this list
        description: Optional description of the list
        icon: Emoji or icon name
        color: Hex color code for UI (e.g., "#FF5733")
        is_default: Whether this is the default list
        is_shared: Whether other users can access this list
        job_count: Denormalized count of jobs in this list
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        archived_at: Soft delete timestamp
    """
    __tablename__ = "saved_jobs_lists"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # List metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    # List configuration
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    job_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships (lazy import to avoid circular dependency)
    user: Mapped[list] = relationship("User", lazy="select", foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_saved_jobs_list_user_name"),
        Index("ix_saved_jobs_lists_user_id", "user_id"),
        Index("ix_saved_jobs_lists_is_default", "is_default"),
        Index("ix_saved_jobs_lists_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """Concise repr for debugging."""
        return f"<SavedJobsList id={self.id!r} user_id={self.user_id!r} name={self.name!r}>"

    def to_dict(self) -> dict:
        """
        Export to dictionary.

        Returns:
            Dict with list metadata

        Example:
            >>> list_data = job_list.to_dict()
            >>> print(f"List has {list_data['job_count']} jobs")
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "is_default": self.is_default,
            "is_shared": self.is_shared,
            "job_count": self.job_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
