"""TrueMatch FastAPI application entrypoint."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import dsar
from app.api.v1.router import api_router
from app.config import settings
from app.core import health
from app.core.config_validator import SecretValidator
from app.core.exceptions import (
    ProblemDetail,
    TrueMatchError,
    problem_detail_from_exception,
)
from app.core.logging import RequestContextMiddleware, SecurityHeadersMiddleware, configure_logging, get_request_id
from app.core.observability import init_sentry, setup_metrics
from app.core.ratelimit import RateLimitMiddleware

logger = logging.getLogger(__name__)

configure_logging()
init_sentry()

app = FastAPI(
    title="TrueMatch API",
    version="0.1.0",
    description="AI-embodied ATS / hiring-assessment platform backend.",
)


# ─ Exception Handlers ────────────────────────────────────────────────────


@app.exception_handler(TrueMatchError)
async def truematch_error_handler(request: Request, exc: TrueMatchError) -> JSONResponse:
    """Handle custom TrueMatchError exceptions."""
    request_id = get_request_id()

    problem_detail = problem_detail_from_exception(exc, request_id)

    logger.error(
        f"{exc.error_type}: {exc.message}",
        extra={
            "request_id": request_id,
            "error_type": exc.error_type,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=problem_detail.model_dump(exclude_none=True),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors (HTTP 422)."""
    request_id = get_request_id()

    # Transform Pydantic errors to field-level error details
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"][1:]),  # Skip 'body'
            "message": error["msg"],
            "type": error["type"],
        })

    problem_detail = ProblemDetail(
        type="validation_error",
        title="Request Validation Failed",
        status=422,
        detail="The request body contains one or more validation errors",
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        instance=str(request.url.path),
        errors=errors,
    )

    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_count": len(errors),
        },
    )

    return JSONResponse(
        status_code=422,
        content=problem_detail.model_dump(exclude_none=True),
        headers={"X-Request-ID": request_id},
    )


# Map plain HTTP status codes to the platform's ProblemDetail error taxonomy so
# every error response (auth, 404, 403, conflict, …) follows ONE contract —
# not just the custom TrueMatchError/validation paths. Backward-compatible:
# `detail` and the HTTP status code are preserved; type/title/instance are added.
_HTTP_STATUS_TYPE: dict[int, tuple[str, str]] = {
    400: ("bad_request", "Bad Request"),
    401: ("authentication_failed", "Authentication Failed"),
    402: ("payment_required", "Payment Required"),
    403: ("authorization_failed", "Authorization Failed"),
    404: ("resource_not_found", "Resource Not Found"),
    409: ("conflict", "Conflict"),
    422: ("validation_error", "Validation Error"),
    429: ("rate_limit_exceeded", "Rate Limit Exceeded"),
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Render plain HTTPExceptions as ProblemDetail (uniform error contract)."""
    request_id = get_request_id()
    error_type, title = _HTTP_STATUS_TYPE.get(
        exc.status_code, ("http_error", "HTTP Error")
    )
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    problem_detail = ProblemDetail(
        type=error_type,
        title=title,
        status=exc.status_code,
        detail=detail,
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        instance=str(request.url.path),
    )
    headers = {"X-Request-ID": request_id}
    if getattr(exc, "headers", None):
        headers.update(exc.headers)
    return JSONResponse(
        status_code=exc.status_code,
        content=problem_detail.model_dump(exclude_none=True),
        headers=headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions (HTTP 500)."""
    request_id = get_request_id()

    # Log the full exception for debugging
    logger.exception(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exc_type": type(exc).__name__,
        },
    )

    # Return generic error response without exposing details
    problem_detail = ProblemDetail(
        type="internal_error",
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred. Please contact support with the request ID.",
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        instance=str(request.url.path),
    )

    return JSONResponse(
        status_code=500,
        content=problem_detail.model_dump(exclude_none=True),
        headers={"X-Request-ID": request_id},
    )


# ─ Middleware ────────────────────────────────────────────────────────────


# Middleware order (outermost first): security headers -> request-id/logging -> rate limit -> CORS.
# CORS is restricted in production to prevent CSRF attacks
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-Request-ID"],
    max_age=3600,  # Cache preflight requests for 1 hour
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

setup_metrics(app)

app.include_router(api_router, prefix="/api/v1")
app.include_router(dsar.router)  # DSAR endpoints (includes /api/v1/dsar prefix)


# ─ Lifecycle Events ──────────────────────────────────────────────────────


# Global references to ingestion workers
_file_monitor = None
_email_ingestor = None


@app.on_event("startup")
async def validate_config():
    """Validate critical configuration at startup.

    Runs before any other startup tasks to fail fast if secrets are misconfigured.
    This prevents deployment with weak or missing credentials.

    Raises:
        ValueError: If critical configuration errors detected
    """
    validator = SecretValidator(settings)
    try:
        validator.validate_all()
        logger.info("✅ Configuration validation passed")
    except ValueError as e:
        logger.critical(f"❌ Configuration validation failed: {e}")
        raise


@app.on_event("startup")
async def start_ingestion_workers():
    """Start file and email ingestion workers on application startup."""
    global _file_monitor, _email_ingestor

    # Start file system monitor for CV/JD folders
    try:
        from app.workers.file_ingestion import FileSystemMonitor

        _file_monitor = FileSystemMonitor()
        _file_monitor.start()
        logger.info("File ingestion worker started")
    except Exception as e:
        logger.error(f"Failed to start file ingestion worker: {e}")

    # Start email ingestion polling loop if configured
    if settings.ingest_imap_host and settings.ingest_imap_user:
        try:
            from app.workers.email_ingestion import EmailIngestor

            _email_ingestor = EmailIngestor()
            asyncio.create_task(_email_ingestor.start_polling())
            logger.info("Email ingestion worker started")
        except Exception as e:
            logger.error(f"Failed to start email ingestion worker: {e}")
    else:
        logger.info("Email ingestion disabled in configuration")

    # Start autonomous agent loop for background task processing
    try:
        from app.agents.autonomous_loop import start_autonomous_loop

        await start_autonomous_loop()
        logger.info("Autonomous agent loop started")
    except Exception as e:
        logger.error(f"Failed to start autonomous loop: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown: stop workers and drain in-flight requests."""
    global _file_monitor, _email_ingestor

    logger.info("Shutdown initiated, stopping ingestion workers...")

    # Stop file monitor
    if _file_monitor:
        try:
            _file_monitor.stop()
            logger.info("File ingestion worker stopped")
        except Exception as e:
            logger.error(f"Error stopping file monitor: {e}")

    # Stop email ingestor
    if _email_ingestor:
        try:
            _email_ingestor.stop_polling()
            logger.info("Email ingestion worker stopped")
        except Exception as e:
            logger.error(f"Error stopping email ingestor: {e}")

    # Stop autonomous agent loop
    try:
        from app.agents.autonomous_loop import stop_autonomous_loop

        await stop_autonomous_loop()
        logger.info("Autonomous agent loop stopped")
    except Exception as e:
        logger.error(f"Error stopping autonomous loop: {e}")

    logger.info("Draining in-flight requests...")
    # Grace period for in-flight requests to complete
    await asyncio.sleep(5)
    logger.info("Shutdown complete")


# ─ Meta Endpoints ────────────────────────────────────────────────────────


@app.get("/livez", tags=["meta"])
async def livez() -> dict:
    """Liveness: the process is up. Cheap; no dependency checks."""
    return {"status": "ok"}


@app.get("/readyz", tags=["meta"])
async def readyz() -> JSONResponse:
    """Readiness: dependencies (DB, Redis) are reachable."""
    ready, components = await health.readiness()
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "components": components},
    )


@app.get("/health", tags=["meta"])
async def health_endpoint() -> dict:
    """Backwards-compatible basic health endpoint."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {"service": "truematch-backend", "docs": "/docs"}
