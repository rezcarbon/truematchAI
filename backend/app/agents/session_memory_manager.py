"""Session memory database persistence layer."""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.session_memory import SessionMemory
from app.models.chat_memory import ChatSessionMemory
from app.core.clock import utcnow

logger = logging.getLogger(__name__)


class SessionMemoryManager:
    """Manages loading and saving session memory to database."""

    @staticmethod
    async def get_or_create(
        session_id: uuid.UUID, db: AsyncSession
    ) -> SessionMemory:
        """Load session memory from DB or create new.

        Args:
            session_id: Chat session ID
            db: Database session

        Returns:
            SessionMemory object with current context
        """
        # Try to load from database
        stmt = select(ChatSessionMemory).where(
            ChatSessionMemory.session_id == session_id
        )
        result = await db.execute(stmt)
        db_record = result.scalar_one_or_none()

        if db_record:
            # Restore from database
            memory = SessionMemory.from_json(str(session_id), db_record.memory_json)
            logger.info(
                "Loaded session memory from DB",
                extra={"session_id": str(session_id)},
            )
        else:
            # Create new memory
            memory = SessionMemory(str(session_id))
            logger.info(
                "Created new session memory",
                extra={"session_id": str(session_id)},
            )

        return memory

    @staticmethod
    async def save(
        session_id: uuid.UUID, memory: SessionMemory, db: AsyncSession
    ) -> None:
        """Save session memory to database.

        Args:
            session_id: Chat session ID
            memory: SessionMemory object to save
            db: Database session
        """
        # Try to find existing record
        stmt = select(ChatSessionMemory).where(
            ChatSessionMemory.session_id == session_id
        )
        result = await db.execute(stmt)
        db_record = result.scalar_one_or_none()

        try:
            now = utcnow()
            if db_record:
                # Update existing
                db_record.memory_json = memory.to_json()
                db_record.updated_at = now
            else:
                # Create new
                db_record = ChatSessionMemory(
                    session_id=session_id,
                    memory_json=memory.to_json(),
                    created_at=now,
                    updated_at=now,
                )
                db.add(db_record)

            await db.commit()
            logger.info(
                "Saved session memory to DB",
                extra={"session_id": str(session_id)},
            )
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to save session memory: {e}",
                extra={"session_id": str(session_id)},
            )
            raise

    @staticmethod
    async def clear(session_id: uuid.UUID, db: AsyncSession) -> None:
        """Delete session memory.

        Args:
            session_id: Chat session ID
            db: Database session
        """
        stmt = select(ChatSessionMemory).where(
            ChatSessionMemory.session_id == session_id
        )
        result = await db.execute(stmt)
        db_record = result.scalar_one_or_none()

        if db_record:
            await db.delete(db_record)
            await db.commit()
            logger.info(
                "Cleared session memory",
                extra={"session_id": str(session_id)},
            )
