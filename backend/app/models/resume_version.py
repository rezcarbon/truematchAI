"""Resume version model for tracking resume history and evolution."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Integer, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class ChangeType(str, enum.Enum):
    """Type of change made to resume."""
    upload = "upload"
    edit = "edit"
    ai_enhancement = "ai_enhancement"
    import_sync = "import"


class ResumeVersion(Base, TimestampMixin):
    """
    Resume version history tracking.

    Stores all versions of a user's resume with full history, enabling:
    - Version comparison and rollback
    - Change tracking and audit trail
    - Quality scoring and improvement tracking
    - Multi-resume support per user

    Attributes:
        id: Unique identifier for this version
        resume_id: Foreign key to the parent resume
        user_id: Foreign key to the user who owns the resume
        version_number: Sequential version number for this resume
        is_current: Whether this is the currently active version
        file_id: Reference to the stored file
        file_name: Original filename when uploaded
        file_size_bytes: Size of the file in bytes
        file_type: MIME type (e.g., "application/pdf")
        source_language: Language specified by user (e.g., "en", "es")
        detected_language: Automatically detected language from content
        parsed_data: Structured resume data (encrypted at rest)
        raw_narrative: Plain text extraction of resume (encrypted at rest)
        supplementary: Additional metadata from parsing (encrypted at rest)
        content_diff: Changes from previous version (encrypted at rest)
        quality_score: Computed quality metric (0-100)
        completeness_percentage: Percentage of expected resume sections present
        sections_detected: Denormalized detection results per section
        change_summary: Human-readable summary of what changed
        change_type: Type of change made
        change_metadata: Additional metadata about the change
        created_by_id: User who created this version
        archived_at: Soft delete timestamp
        created_at: When this version was created
        updated_at: When this version was last updated
    """
    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    resume_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Version tracking
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # File and parsing information
    file_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Language and content
    source_language: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    detected_language: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    # PII at rest — encrypted using AES-256-GCM
    parsed_data: Mapped[Optional[dict]] = mapped_column(EncryptedJSON, nullable=True)
    raw_narrative: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    supplementary: Mapped[Optional[dict]] = mapped_column(EncryptedJSON, nullable=True)
    # Content diff tracking changes from previous version (encrypted)
    content_diff: Mapped[Optional[dict]] = mapped_column(EncryptedJSON, nullable=True)

    # Metadata and quality scoring
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completeness_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sections_detected: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Change tracking
    change_summary: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    change_type: Mapped[ChangeType] = mapped_column(String(50), nullable=False, default=ChangeType.upload)
    change_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Audit trail
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships (lazy import to avoid circular dependency)
    resume: Mapped[list] = relationship("Resume", lazy="select", foreign_keys=[resume_id])
    created_by: Mapped[list] = relationship("User", lazy="select", foreign_keys=[created_by_id])

    __table_args__ = (
        Index("ix_resume_versions_resume_version", "resume_id", "version_number"),
        Index("ix_resume_versions_resume_id", "resume_id"),
        Index("ix_resume_versions_user_id", "user_id"),
        Index("ix_resume_versions_is_current", "is_current"),
        Index("ix_resume_versions_change_type", "change_type"),
        Index("ix_resume_versions_created_at", "created_at"),
        Index("ix_resume_versions_archived_at", "archived_at"),
        Index("ix_resume_versions_user_current", "user_id", "is_current"),
        Index("ix_resume_versions_resume_created", "resume_id", "created_at"),
    )

    def __repr__(self) -> str:
        """Concise repr for debugging."""
        return (
            f"<ResumeVersion id={self.id!r} resume_id={self.resume_id!r} "
            f"version={self.version_number} is_current={self.is_current}>"
        )

    @classmethod
    def get_by_version(
        cls,
        session,
        resume_id: uuid.UUID,
        version_number: int,
    ) -> Optional[ResumeVersion]:
        """
        Retrieve a specific version of a resume.

        Args:
            session: SQLAlchemy async session
            resume_id: Parent resume ID
            version_number: Target version number

        Returns:
            ResumeVersion if found, None otherwise

        Example:
            >>> version = ResumeVersion.get_by_version(session, resume_id, 2)
            >>> if version:
            ...     print(f"Quality score: {version.quality_score}")
        """
        return session.query(cls).filter(
            cls.resume_id == resume_id,
            cls.version_number == version_number,
        ).first()

    def compute_diff_to_current(self) -> Optional[dict]:
        """
        Compute structural diff between this version and the current version.

        Reconstructs what changed from this version to the current one.
        Returns None if this is already the current version.

        Returns:
            Dictionary with 'added', 'removed', 'modified' keys showing changes,
            or None if this version is current.

        Example:
            >>> version = session.query(ResumeVersion).filter_by(version_number=1).first()
            >>> diff = version.compute_diff_to_current()
            >>> if diff:
            ...     print(f"Added sections: {diff.get('added', [])}")
        """
        if self.is_current:
            return None

        if not self.content_diff:
            return {"message": "No diff recorded for this version transition"}

        return self.content_diff

    def get_current_version(self, session) -> Optional[ResumeVersion]:
        """
        Get the current version of this resume.

        Returns:
            Current ResumeVersion for this resume, or None

        Example:
            >>> current = version.get_current_version(session)
            >>> if current and current.id != version.id:
            ...     print("This is not the current version")
        """
        return session.query(ResumeVersion).filter(
            ResumeVersion.resume_id == self.resume_id,
            ResumeVersion.is_current == True,
        ).first()

    def validate_content(self) -> dict:
        """
        Validate completeness and quality of parsed content.

        Returns:
            Dict with validation results: {'is_valid': bool, 'issues': list, 'score': float}

        Example:
            >>> result = version.validate_content()
            >>> if not result['is_valid']:
            ...     print(f"Issues found: {result['issues']}")
        """
        issues = []
        score = self.quality_score or 0.0

        # Check required sections
        if not self.parsed_data:
            issues.append("No parsed data available")
            score = 0.0
        elif isinstance(self.sections_detected, dict):
            if not self.sections_detected.get("contact_info"):
                issues.append("Missing contact information")
            if not self.sections_detected.get("experience"):
                issues.append("Missing work experience")
            if not self.sections_detected.get("education"):
                issues.append("Missing education")

        # Check completeness
        if self.completeness_percentage and self.completeness_percentage < 50:
            issues.append(f"Low completeness: {self.completeness_percentage}%")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "score": score,
        }

    def to_dict(self) -> dict:
        """
        Export version metadata (not encrypted fields) to dictionary.

        Returns:
            Dict with all non-encrypted metadata about this version

        Example:
            >>> version_dict = version.to_dict()
            >>> print(f"Version {version_dict['version_number']} by {version_dict['created_by_id']}")
        """
        return {
            "id": str(self.id),
            "resume_id": str(self.resume_id),
            "user_id": str(self.user_id),
            "version_number": self.version_number,
            "is_current": self.is_current,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "quality_score": self.quality_score,
            "completeness_percentage": self.completeness_percentage,
            "change_type": self.change_type.value if isinstance(self.change_type, ChangeType) else self.change_type,
            "change_summary": self.change_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by_id": str(self.created_by_id) if self.created_by_id else None,
        }
