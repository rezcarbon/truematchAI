"""Resume model."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON, EncryptedText


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # PII at rest — encrypted. supplementary holds the full extracted resume text.
    parsed_data: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    raw_narrative: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    supplementary: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)

    __table_args__ = (
        Index("ix_resumes_user_id", "user_id"),
    )
