"""
Job scraping models for tracking scraping runs and mass uploads.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobSourceType(str, Enum):
    """Supported job data sources"""
    usajobs = "usajobs"
    ziprecruiter = "ziprecruiter"
    theirstack = "theirstack"
    linkedin = "linkedin"
    indeed = "indeed"
    glassdoor = "glassdoor"
    other = "other"


class UploadType(str, Enum):
    """Supported upload formats"""
    csv = "csv"
    json = "json"
    api = "api"


class BatchStatus(str, Enum):
    """Status of scraping runs and upload batches"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobScrapingConfig(Base):
    """Configuration for a job scraping source"""
    __tablename__ = "job_scraping_config"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Source type
    source_type: Mapped[JobSourceType] = mapped_column(String(50))

    # Enable/disable
    enabled: Mapped[bool] = mapped_column(default=False)

    # Configuration (API keys, filters, etc.)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    # Scheduling info
    poll_hours: Mapped[int] = mapped_column(default=24)
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Legal approval (required for direct scrapers)
    legal_approved: Mapped[bool] = mapped_column(default=False)
    legal_approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.now(datetime.timezone.utc)
    )


class ScrapingRun(Base):
    """Track individual scraping runs"""
    __tablename__ = "scraping_run"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Reference to config
    config_id: Mapped[uuid.UUID] = mapped_column()  # Foreign key to JobScrapingConfig

    # Run status
    status: Mapped[BatchStatus] = mapped_column(String(50), default=BatchStatus.pending)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Statistics
    jobs_found: Mapped[int] = mapped_column(default=0)
    jobs_processed: Mapped[int] = mapped_column(default=0)
    jobs_failed: Mapped[int] = mapped_column(default=0)

    # Error tracking
    errors: Mapped[dict] = mapped_column(JSON, default=dict)

    # Tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(datetime.timezone.utc)
    )


class MassUploadBatch(Base):
    """Track mass upload batches (CSV, JSON, API)"""
    __tablename__ = "mass_upload_batch"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Upload info
    upload_type: Mapped[UploadType] = mapped_column(String(50))
    user_id: Mapped[uuid.UUID] = mapped_column()  # Foreign key to User
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Field mapping for CSV (JSON structure mapping columns to fields)
    field_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Processing status
    status: Mapped[BatchStatus] = mapped_column(String(50), default=BatchStatus.pending)

    # Statistics
    total_rows: Mapped[int] = mapped_column(default=0)
    processed_rows: Mapped[int] = mapped_column(default=0)
    failed_rows: Mapped[int] = mapped_column(default=0)
    duplicate_rows: Mapped[int] = mapped_column(default=0)

    # Error tracking
    errors: Mapped[dict] = mapped_column(JSON, default=dict)

    # Tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(datetime.timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobDeduplication(Base):
    """Track job fingerprints to prevent duplicates"""
    __tablename__ = "job_deduplication"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Job fingerprint (hash of title + company + normalized content)
    fingerprint: Mapped[str] = mapped_column(String(256), unique=True, index=True)

    # External IDs from different sources (for tracking where job came from)
    external_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    # Example: {"usajobs": "123456", "linkedin": "789012", "indeed": "345678"}

    # Reference to ingest queue item
    ingest_queue_item_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    # Tracking
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(datetime.timezone.utc)
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.now(datetime.timezone.utc)
    )
    seen_count: Mapped[int] = mapped_column(default=1)


class UploadFieldMapping(Base):
    """Pre-configured field mappings for CSV uploads"""
    __tablename__ = "upload_field_mapping"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Mapping name (e.g., "LinkedIn Export", "ZipRecruiter CSV")
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Field mapping configuration
    # Example: {"Job Title": "title", "Description": "description", ...}
    field_mapping: Mapped[dict] = mapped_column(JSON)

    # Required fields
    required_fields: Mapped[list] = mapped_column(JSON, default=list)

    # User-created vs. system
    is_system: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    # Tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(datetime.timezone.utc)
    )
