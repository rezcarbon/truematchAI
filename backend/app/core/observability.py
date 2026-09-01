"""Optional error tracking (Sentry) and metrics (Prometheus).

Both are opt-in and lazily imported, so the app starts cleanly whether or not
the optional packages are installed or configured. Enable Sentry by setting
SENTRY_DSN; metrics are exposed at /metrics when METRICS_ENABLED and the
prometheus-client package is present.
"""
from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.config import settings

logger = logging.getLogger("truematch.observability")


def init_sentry() -> None:
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
            send_default_pii=False,  # never forward PII to the error tracker
        )
        logger.info("Sentry initialised.")
    except ImportError:
        logger.warning("SENTRY_DSN set but sentry-sdk is not installed; skipping.")


def setup_metrics(app) -> None:
    if not settings.metrics_enabled:
        return
    try:
        from prometheus_client import (
            CONTENT_TYPE_LATEST,
            Counter,
            Histogram,
            generate_latest,
        )
    except ImportError:
        logger.warning("METRICS_ENABLED but prometheus-client is not installed; skipping.")
        return

    requests_total = Counter(
        "truematch_http_requests_total",
        "HTTP requests",
        ["method", "status"],
    )
    latency = Histogram(
        "truematch_http_request_duration_seconds",
        "HTTP request latency",
        ["method"],
    )

    class _MetricsMiddleware(BaseHTTPMiddleware):
        def __init__(self, inner: ASGIApp) -> None:
            super().__init__(inner)

        async def dispatch(self, request: Request, call_next):
            start = time.perf_counter()
            response = await call_next(request)
            latency.labels(request.method).observe(time.perf_counter() - start)
            requests_total.labels(request.method, str(response.status_code)).inc()
            return response

    app.add_middleware(_MetricsMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:  # pragma: no cover - thin glue
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
