"""External ATS connector endpoints — status + import (recruiter/admin)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.deps import CurrentRecruiter, DBSession
from app.services.ats_connectors import connector_status, get_connector
from app.services.ats_connectors.importer import import_candidates, import_jobs

logger = logging.getLogger("truematch.connectors")
router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("")
async def list_connectors(user: CurrentRecruiter) -> dict:
    """List known ATS connectors and whether each is configured."""
    return {"connectors": connector_status()}


def _require_configured(provider: str):
    connector = get_connector(provider)
    if connector is None:
        raise HTTPException(status_code=404, detail=f"Unknown connector '{provider}'")
    if not connector.is_configured:
        raise HTTPException(
            status_code=503,
            detail=f"Connector '{provider}' is not configured (missing API key).",
        )
    return connector


@router.post("/{provider}/import-jobs")
async def import_provider_jobs(
    provider: str, user: CurrentRecruiter, db: DBSession
) -> dict:
    """Pull the provider's jobs and upsert them as positions (idempotent)."""
    connector = _require_configured(provider)
    try:
        jobs = await __import__("asyncio").to_thread(connector.list_jobs)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"{provider} job fetch failed: {exc}") from exc
    return await import_jobs(db, connector.provider, jobs, user)


@router.post("/{provider}/import-candidates")
async def import_provider_candidates(
    provider: str, user: CurrentRecruiter, db: DBSession, job_external_id: str | None = None
) -> dict:
    """Pull the provider's candidates and upsert them as resumes+applications."""
    connector = _require_configured(provider)
    try:
        candidates = await __import__("asyncio").to_thread(
            connector.list_candidates, job_external_id
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"{provider} candidate fetch failed: {exc}") from exc
    return await import_candidates(db, connector.provider, candidates, user)
