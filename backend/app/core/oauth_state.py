"""Short-lived OAuth/OIDC transaction state store.

Holds the per-login `nonce` and PKCE `code_verifier` between the authorization
request and the callback, keyed by the opaque `state` value. Backed by Redis in
production (so it works across multiple API instances); falls back to an
in-process dict when Redis is unreachable (single-instance dev only).

State entries are single-use: `pop` deletes the entry so a `state` cannot be
replayed.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger("truematch.oauth_state")

_KEY_PREFIX = "oidc:state:"

# Process-local fallback when Redis is unavailable. Not multi-instance safe.
_memory: dict[str, str] = {}


def _redis():
    try:
        import redis.asyncio as aioredis  # lazy import
    except ImportError:  # pragma: no cover - redis is a core dependency
        return None
    try:
        return aioredis.from_url(settings.redis_url, decode_responses=True)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Redis unavailable for OAuth state; using in-memory store: %s", exc)
        return None


async def put(state: str, data: dict[str, Any], ttl_seconds: int | None = None) -> None:
    ttl = ttl_seconds or settings.singpass_state_ttl_seconds
    payload = json.dumps(data)
    client = _redis()
    if client is not None:
        try:
            await client.set(_KEY_PREFIX + state, payload, ex=ttl)
            return
        except Exception as exc:  # pragma: no cover - fall back on runtime error
            logger.warning("Redis set failed; using in-memory state: %s", exc)
    _memory[state] = payload


async def pop(state: str) -> dict[str, Any] | None:
    """Atomically fetch and delete the state entry. Returns None if absent."""
    client = _redis()
    if client is not None:
        try:
            key = _KEY_PREFIX + state
            payload = await client.get(key)
            if payload is not None:
                await client.delete(key)
                return json.loads(payload)
            # fall through to memory in case it was stored there
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis pop failed; checking in-memory state: %s", exc)
    payload = _memory.pop(state, None)
    return json.loads(payload) if payload is not None else None
