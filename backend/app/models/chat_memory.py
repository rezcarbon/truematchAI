"""Chat session memory persistence model."""
from __future__ import annotations

import json
import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin, uuid_pk


class ChatSessionMemory(Base, TimestampMixin):
    """Persists conversation context across messages within a session."""

    __tablename__ = "chat_session_memories"

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    memory_json: Mapped[str] = mapped_column(Text, nullable=False)

    def to_dict(self) -> dict:
        """Parse JSON memory to dict."""
        return json.loads(self.memory_json)

    @classmethod
    def from_dict(cls, session_id: uuid.UUID, memory_dict: dict) -> ChatSessionMemory:
        """Create memory object from dict."""
        return cls(
            session_id=session_id,
            memory_json=json.dumps(memory_dict, default=str),
        )
