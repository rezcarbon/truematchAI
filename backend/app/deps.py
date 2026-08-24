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


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
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
    import logging
    logger = logging.getLogger(__name__)

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        logger.info(f"JWT decoded successfully: sub={payload.get('sub')}, type={payload.get('type')}")
    except JWTError as e:
        logger.error(f"JWT decode failed: {e}")
        raise credentials_exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        logger.error(f"Token type mismatch: expected {ACCESS_TOKEN_TYPE}, got {payload.get('type')}")
        raise credentials_exc
    sub = payload.get("sub")
    if not sub:
        logger.error("No 'sub' claim in token")
        raise credentials_exc
    try:
        user_id = uuid.UUID(sub)
        logger.info(f"Converted sub to UUID: {user_id}")
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to parse UUID from sub: {e}")
        raise credentials_exc

    user = await db.get(User, user_id)
    if user is None:
        logger.error(f"User not found in database: {user_id}")
        raise credentials_exc
    logger.info(f"User authenticated: {user.email}")
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


async def get_current_recruiter(
    user: Annotated[User, Depends(require_role(UserRole.recruiter, UserRole.admin))],
) -> User:
    """Recruiter-or-admin gate for staff-only ATS endpoints."""
    return user


CurrentRecruiter = Annotated[User, Depends(get_current_recruiter)]
