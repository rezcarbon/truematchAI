"""Shared FastAPI dependencies: database session, Redis, and current-user resolution."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import ACCESS_TOKEN_TYPE, JWTError, decode_token
from app.database import get_session
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_redis() -> AsyncGenerator[redis.Redis[bytes], None]:
    """Get Redis connection for token denylist and caching.

    Yields:
        redis.asyncio.Redis instance for async operations

    Raises:
        redis.ConnectionError: If Redis is unavailable
    """
    client = redis.from_url(settings.redis_url, decode_responses=False)
    try:
        yield client
    finally:
        await client.close()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSession,
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise credentials_exc
    sub = payload.get("sub")
    if not sub:
        raise credentials_exc
    try:
        user_id = uuid.UUID(sub)
    except (ValueError, TypeError):
        raise credentials_exc

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    """Dependency factory enforcing that the current user has one of the given roles."""

    async def _checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _checker


async def get_current_admin(
    user: Annotated[User, Depends(require_role(UserRole.admin))],
) -> User:
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
