"""Password hashing and JWT encode/decode.

Uses the `bcrypt` library directly (passlib is unmaintained and breaks with
bcrypt >= 4.1). bcrypt hashes at most 72 bytes; longer passwords are truncated
to that boundary, which is bcrypt's standard, well-understood behaviour.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

_BCRYPT_MAX_BYTES = 72


def _prepare(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password_sync(password: str) -> str:
    """Synchronous password hashing (blocking)."""
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("ascii")


async def hash_password(password: str) -> str:
    """Hash password asynchronously to avoid blocking the event loop.

    bcrypt.hashpw is CPU-intensive and blocking, so we run it in a thread pool.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, hash_password_sync, password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta, **extra: Any) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        **extra,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, **extra: Any) -> str:
    return _create_token(
        subject,
        ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.access_token_expire_minutes),
        **extra,
    )


def create_refresh_token(subject: str, **extra: Any) -> str:
    return _create_token(
        subject,
        REFRESH_TOKEN_TYPE,
        timedelta(days=settings.refresh_token_expire_days),
        **extra,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT, raising JWTError on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def verify_token_from_websocket(token: str) -> str | None:
    """
    Verify JWT token from WebSocket connection and return user_id.
    Returns None if token is invalid or missing subject.
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id:
            return user_id
        return None
    except JWTError:
        return None


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token_from_websocket",
    "JWTError",
    "ACCESS_TOKEN_TYPE",
    "REFRESH_TOKEN_TYPE",
]
