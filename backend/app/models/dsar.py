"""Data Subject Access Request (DSAR) model for GDPR Article 15/17 compliance."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class DSARStatus(str, enum.Enum):
    """Status progression of a Data Subject Access Request."""
    received = "received"
    processing = "processing"
    ready_for_download = "ready_for_download"
    completed = "completed"


class DSARRequest(Base, TimestampMixin):
    """
    Data Subject Access Request (DSAR) for GDPR Article 15 (access) and
    Article 17 (right to be forgotten/deletion) compliance.

    Tracks the lifecycle of a DSAR from receipt through processing to completion,
    including the location of the exported data archive for download.
    """
    __tablename__ = "dsar_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    request_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[DSARStatus] = mapped_column(
        SAEnum(DSARStatus, name="dsar_status"),
        default=DSARStatus.received,
        nullable=False,
    )
    data_export_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_dsar_requests_user_id", "user_id"),
        Index("ix_dsar_requests_status", "status"),
    )
