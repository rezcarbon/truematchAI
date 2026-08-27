"""Fixed-window per-client rate limiting.

Counts requests per client IP within a 60-second window. Uses Redis (so the
limit is shared across API instances) and falls back to an in-process counter
when Redis is unavailable. Probe/metrics endpoints are exempt.

Returns HTTP 429 with a `Retry-After` header when the limit is exceeded.

This is implemented as pure ASGI middleware (not BaseHTTPMiddleware) to avoid
interfering with multipart request streaming.
"""
from __future__ import annotations

import json
import logging
import time

from starlette.types import ASGIApp, Receive, Scope, Send

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


class RateLimitMiddleware:
    """Pure ASGI middleware for rate limiting by client IP.

    Avoids BaseHTTPMiddleware to prevent interference with multipart streaming.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._limit = settings.rate_limit_per_minute

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract path and method from scope
        path = scope.get("path", "")
        method = scope.get("method", "")

        # Exempt OPTIONS (CORS preflight), health checks, and certain prefixes
        if (
            not settings.rate_limit_enabled
            or self._limit <= 0
            or method == "OPTIONS"  # Always allow CORS preflight
            or path.startswith(_EXEMPT_PREFIXES)
        ):
            await self.app(scope, receive, send)
            return

        # Extract client IP from scope
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        # Check rate limit
        count, retry_after = await _incr(client_ip, self._limit)
        if count > self._limit:
            # Send 429 response
            response_body = json.dumps({"detail": "Rate limit exceeded"})
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"retry-after", str(retry_after).encode()),
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": response_body.encode(),
                }
            )
            return

        # Allow request to proceed
        await self.app(scope, receive, send)
