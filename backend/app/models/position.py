"""Position (job) model."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class PositionStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    closed = "closed"
    archived = "archived"


class Position(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Nullable: candidate self-assessment positions have no owning company.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    jd_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jd_issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[PositionStatus] = mapped_column(
        SAEnum(PositionStatus, name="position_status"),
        default=PositionStatus.draft,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_positions_company_id", "company_id"),
        Index("ix_positions_status", "status"),
    )
