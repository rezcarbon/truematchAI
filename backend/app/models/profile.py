"""Capability profile model — a candidate's portable, shareable capability summary."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class ProfileVisibility(str, enum.Enum):
    private = "private"
    link = "link"
    public = "public"


class CapabilityProfile(Base, TimestampMixin):
    __tablename__ = "capability_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    narrative: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    trajectory_summary: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    top_capabilities: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    assessment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    visibility: Mapped[ProfileVisibility] = mapped_column(
        SAEnum(ProfileVisibility, name="profile_visibility"),
        default=ProfileVisibility.private,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_capability_profiles_user_id", "user_id", unique=True),
        Index("ix_capability_profiles_share_token", "share_token", unique=True),
    )
