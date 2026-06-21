"""Durable per-user agent memory (cross-session).

LLM-curated summary of durable facts about how this user works — preferences,
active focus, recurring intents — merged periodically from chat sessions and
injected into the agent's system prompt each turn. Encrypted at rest like other
personal content; user-erasable.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk
from app.models._types import EncryptedJSON


class UserAgentMemory(Base, TimestampMixin):
    __tablename__ = "user_agent_memory"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # {"facts": ["..."], "preferences": ["..."], "active_focus": ["..."]}
    memory: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    merge_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("user_id", name="uq_user_agent_memory_user"),)
