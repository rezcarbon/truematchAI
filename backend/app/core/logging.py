"""Structured logging configuration and request-correlation middleware.

Emits one-line JSON logs in production (parseable by log aggregators) and a
human-readable format in dev. Each request is tagged with a correlation id that
is attached to every log record produced while handling it and returned in the
`X-Request-ID` response header.

Both middleware implementations use pure ASGI (not BaseHTTPMiddleware) to avoid
interfering with multipart request streaming.
"""
from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return _request_id.get()


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())
    if settings.log_json:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
        )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())


class RequestContextMiddleware:
    """Pure ASGI middleware: assign/propagate request ID and log access lines with latency.

    Sets the request ID context var before the app runs and logs the access line
    after the response headers are sent. Uses pure ASGI (not BaseHTTPMiddleware)
    to avoid interfering with multipart streaming.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._log = logging.getLogger("truematch.access")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request ID from headers or generate one
        headers = dict(scope.get("headers", []))
        rid = None
        for name, value in scope.get("headers", []):
            if name.lower() == b"x-request-id":
                rid = value.decode()
                break
        if not rid:
            rid = uuid.uuid4().hex

        # Set the request ID context var for this request
        token = _request_id.set(rid)
        start = time.perf_counter()
        response_status = None

        async def send_with_logging(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
                # Add X-Request-ID header to response
                headers_list = list(message.get("headers", []))
                headers_list.append((b"x-request-id", rid.encode()))
                message = {**message, "headers": headers_list}

            await send(message)

        try:
            await self.app(scope, receive, send_with_logging)
            # Log after response is sent (while context var is still set)
            if response_status is not None:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                method = scope.get("method", "UNKNOWN")
                path = scope.get("path", "/")
                self._log.info(
                    "%s %s -> %s (%.1fms)",
                    method,
                    path,
                    response_status,
                    elapsed_ms,
                )
        except Exception as e:
            self._log.exception(
                f"Exception in middleware for {scope.get('method', 'UNKNOWN')} "
                f"{scope.get('path', '/')}: {type(e).__name__}: {e}"
            )
            raise
        finally:
            _request_id.reset(token)


class SecurityHeadersMiddleware:
    """Pure ASGI middleware: add security headers to all responses.

    Adds HSTS, CSP, X-Frame-Options, and other security headers to every HTTP
    response. Uses pure ASGI (not BaseHTTPMiddleware) to avoid interfering with
    multipart streaming.
    """

    # Security headers as bytes for efficient ASGI transmission
    _SECURITY_HEADERS = [
        (b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload"),
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"x-xss-protection", b"1; mode=block"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (b"permissions-policy", b"geolocation=(), microphone=(), camera=()"),
        (
            b"content-security-policy",
            b"default-src 'self'; "
            b"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            b"style-src 'self' 'unsafe-inline'; "
            b"img-src 'self' data: https:; "
            b"font-src 'self' data:; "
            b"connect-src 'self'; "
            b"frame-ancestors 'none'; "
            b"base-uri 'self'; "
            b"form-action 'self'",
        ),
    ]

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Add security headers to the response
                headers_list = list(message.get("headers", []))
                headers_list.extend(self._SECURITY_HEADERS)
                message = {**message, "headers": headers_list}

            await send(message)

        await self.app(scope, receive, send_with_headers)
