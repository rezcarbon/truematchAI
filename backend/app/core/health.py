"""Liveness/readiness checks for orchestration probes.

`liveness` answers "is the process up". `readiness` answers "can it serve
traffic" by checking the database and Redis. Failures are caught and reported as
component booleans so the probe can return 503 without raising.
"""
from __future__ import annotations

import logging

from sqlalchemy import text

from app.config import settings
from app.database import engine

logger = logging.getLogger("truematch.health")


async def check_db() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB readiness check failed: %s", exc)
        return False


async def check_redis() -> bool:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url)
        try:
            return bool(await client.ping())
        finally:
            await client.aclose()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis readiness check failed: %s", exc)
        return False


async def check_s3() -> bool:
    """Check S3 bucket accessibility (if configured)."""
    if not settings.s3_bucket:
        # S3 not configured, skip check
        return True

    try:
        import aioboto3

        session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        async with session.client("s3") as s3:
            await s3.head_bucket(Bucket=settings.s3_bucket)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("S3 readiness check failed: %s", exc)
        return False


async def check_llm() -> bool:
    """Check LLM API availability (if enabled)."""
    if settings.llm_force_mock:
        # LLM mocking enabled, skip check
        return True

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        # Use list models endpoint (cheap, doesn't consume tokens)
        client.models.list()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM readiness check failed: %s", exc)
        return False


async def check_singpass() -> bool:
    """Check Singpass OIDC connectivity (if configured)."""
    if not settings.singpass_client_id:
        # Singpass not configured, skip check
        return True

    try:
        # Singpass connectivity check via OIDC discovery endpoint
        import httpx

        issuer_url = settings.singpass_issuer
        discovery_url = f"{issuer_url}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(discovery_url)
            return response.status_code == 200
    except Exception as exc:  # noqa: BLE001
        logger.warning("Singpass readiness check failed: %s", exc)
        return False


async def readiness() -> tuple[bool, dict[str, bool]]:
    """Check dependencies for readiness.

    Readiness gates ONLY on components required to serve traffic — the database
    and Redis. Optional integrations (S3 file storage [DB fallback exists], the
    LLM [has a configured failover provider], and Singpass [optional auth]) are
    reported for observability but do NOT 503 the instance: a flaky optional
    dependency must not pull every pod out of the load-balancer rotation.
    """
    components = {
        "database": await check_db(),
        "redis": await check_redis(),
        "s3": await check_s3(),
        "llm": await check_llm(),
        "singpass": await check_singpass(),
    }
    required = ("database", "redis")
    ready = all(components[c] for c in required)
    return ready, components
