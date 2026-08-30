"""Chat message and conversation models."""
from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.core.clock import utcnow
from app.models.base import Base


class ConversationStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    closed = "closed"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Conversation(Base):
    """Chat conversation."""
    __tablename__ = "conversations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=lambda: UUID(int=0))
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.active)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[user_id])


class Message(Base):
    """Chat message."""
    __tablename__ = "messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=lambda: UUID(int=0))
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(MessageRole), default=MessageRole.user, nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", foreign_keys=[user_id])


# Legacy chat models (kept for backward compatibility with existing code)
class ChatSession(Base):
    """Legacy chat session model."""
    __tablename__ = "chat_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=lambda: UUID(int=0))
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", foreign_keys=[user_id])


class ChatMessage(Base):
    """Legacy chat message model."""
    __tablename__ = "chat_messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=lambda: UUID(int=0))
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    actions_taken = Column(JSONB, nullable=True)
    message_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")
