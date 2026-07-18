"""Async SQLAlchemy engine and session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4, UUID

from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from app.config import settings


def uuid_pk() -> Mapped[UUID]:
    """Create a UUID primary key column with PostgreSQL UUID type."""
    return mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    # Connection pool configuration for production
    # pool_size: number of connections to keep in the pool (tuned for 50 concurrent requests)
    # max_overflow: additional connections to allow under load (peak burst protection)
    # pool_pre_ping: validate connections before using them (prevent stale connections)
    # pool_recycle: recycle connections older than 3600s (1 hour) to prevent DB timeouts
    # pool_timeout: wait up to 30 seconds for a connection from the pool
    pool_size=50,  # Increased from 20 for production load
    max_overflow=20,  # Increased from 10 for better peak handling
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,  # 30s timeout before failing with connection error
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session, committing on success and rolling back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
