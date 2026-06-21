"""Fixed-window per-client rate limiting.

Counts requests per client IP within a 60-second window. Uses Redis (so the
limit is shared across API instances) and falls back to an in-process counter
when Redis is unavailable. Probe/metrics endpoints are exempt.

Returns HTTP 429 with a `Retry-After` header when the limit is exceeded.
"""
from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.config import settings

logger = logging.getLogger("truematch.ratelimit")

_EXEMPT_PREFIXES = ("/health", "/livez", "/readyz", "/metrics")
_WINDOW = 60

# In-memory fallback: {key: (window_start_epoch, count)}
_memory: dict[str, tuple[int, int]] = {}


def _redis():
    try:
        import redis.asyncio as aioredis

        return aioredis.from_url(settings.redis_url)
    except Exception:  # pragma: no cover - redis is a core dep
        return None


async def _incr(key: str, limit: int) -> tuple[int, int]:
    """Return (count, retry_after_seconds) for the current window."""
    now = int(time.time())
    window = now - (now % _WINDOW)
    redis_key = f"ratelimit:{key}:{window}"
    client = _redis()
    if client is not None:
        try:
            count = await client.incr(redis_key)
            if count == 1:
                await client.expire(redis_key, _WINDOW)
            await client.aclose()
            return count, _WINDOW - (now % _WINDOW)
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis rate-limit unavailable; using in-memory: %s", exc)
    start, count = _memory.get(key, (window, 0))
    if start != window:
        start, count = window, 0
    count += 1
    _memory[key] = (start, count)
    return count, _WINDOW - (now % _WINDOW)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._limit = settings.rate_limit_per_minute

    async def dispatch(self, request: Request, call_next):
        # Exempt OPTIONS (CORS preflight), health checks, and certain prefixes
        if (
            not settings.rate_limit_enabled
            or self._limit <= 0
            or request.method == "OPTIONS"  # Always allow CORS preflight
            or request.url.path.startswith(_EXEMPT_PREFIXES)
        ):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        count, retry_after = await _incr(client_ip, self._limit)
        if count > self._limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
