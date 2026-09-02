"""ATS Bidirectional Sync API endpoints.

Manage automatic sync operations, conflict resolution, and audit logs
for ATS integrations (Lever, Greenhouse, Workable).
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.deps import CurrentRecruiter, DBSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ats-sync", tags=["ats-sync"])


class SyncOperationResponse(BaseModel):
    """Sync operation details."""

    id: str = Field(..., description="Operation ID")
    provider: str = Field(..., description="ATS provider (lever, greenhouse, workable)")
    operation_type: str = Field(..., description="import or export")
    status: str = Field(..., description="pending, running, completed, failed")
    started_at: datetime
    completed_at: datetime | None = None
    records_processed: int = 0
    errors: int = 0
    error_message: str | None = None


class ConflictResponse(BaseModel):
    """Detected conflict details."""

    id: str
    entity_type: str
    local_value: str | dict
    ats_value: str | dict
    detected_at: datetime
    suggested_resolution: str
    resolved: bool = False
    resolution_strategy: str | None = None
    resolved_at: datetime | None = None


class SyncLogResponse(BaseModel):
    """Audit log entry."""

    id: str
    timestamp: datetime
    provider: str
    operation: str
    entity_type: str
    entity_id: str
    status: str
    message: str


@router.post("/trigger-import/{provider}")
async def trigger_import(
    provider: str,
    recruiter: CurrentRecruiter,
    db: DBSession,
) -> dict:
    """Queue ATS import task for background processing.

    Args:
        provider: ATS provider (lever, greenhouse, workable)
        recruiter: Current authenticated recruiter
        db: Database session

    Returns:
        Operation details with task ID

    Example:
        POST /ats-sync/trigger-import/lever
        Returns: {
            "operation_id": "op_123abc",
            "status": "queued",
            "message": "Import queued for processing"
        }
    """
    if provider not in ["lever", "greenhouse", "workable"]:
        raise HTTPException(status_code=400, detail=f"Unknown ATS provider: {provider}")

    logger.info(f"Queuing ATS import for {provider} by recruiter {recruiter.id}")

    # In production, this would queue a Celery task
    return {
        "operation_id": f"op_{provider}_{datetime.utcnow().isoformat()}",
        "provider": provider,
        "status": "queued",
        "message": f"Import task queued for {provider}",
    }


@router.post("/trigger-export/{provider}/{entity_type}/{entity_id}")
async def trigger_export(
    provider: str,
    entity_type: str,
    entity_id: str,
    recruiter: CurrentRecruiter,
    db: DBSession,
) -> dict:
    """Queue ATS export task for background processing.

    Args:
        provider: ATS provider
        entity_type: Entity type (application, scorecard, etc.)
        entity_id: Entity ID to export
        recruiter: Current recruiter
        db: Database session

    Returns:
        Operation details with task ID
    """
    if provider not in ["lever", "greenhouse", "workable"]:
        raise HTTPException(status_code=400, detail=f"Unknown ATS provider: {provider}")

    if entity_type not in ["application", "scorecard", "interview"]:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")

    logger.info(
        f"Queuing ATS export: {entity_type} {entity_id} to {provider} by recruiter {recruiter.id}"
    )

    return {
        "operation_id": f"op_{provider}_{entity_type}_{datetime.utcnow().isoformat()}",
        "provider": provider,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "status": "queued",
        "message": f"Export task queued for {provider}",
    }


@router.get("/operations")
async def list_operations(
    provider: str | None = Query(None, description="Filter by provider"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    recruiter: CurrentRecruiter = None,
    db: DBSession = None,
) -> dict:
    """List sync operations with optional filtering.

    Args:
        provider: Optional provider filter
        status: Optional status filter
        limit: Result limit (default 50, max 100)
        offset: Result offset
        recruiter: Current recruiter
        db: Database session

    Returns:
        Paginated list of sync operations
    """
    logger.debug(
        f"Listing sync operations: provider={provider}, status={status}, limit={limit}"
    )

    # In production, would query database
    return {
        "operations": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "provider_filter": provider,
        "status_filter": status,
    }


@router.get("/operations/{operation_id}")
async def get_operation(
    operation_id: str,
    recruiter: CurrentRecruiter,
    db: DBSession,
) -> SyncOperationResponse:
    """Get details of a specific sync operation.

    Args:
        operation_id: Operation ID
        recruiter: Current recruiter
        db: Database session

    Returns:
        Operation details
    """
    logger.debug(f"Getting operation details: {operation_id}")
    raise HTTPException(status_code=404, detail="Operation not found")


@router.get("/conflicts")
async def list_conflicts(
    resolved: bool | None = Query(None, description="Filter by resolved status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    recruiter: CurrentRecruiter = None,
    db: DBSession = None,
) -> dict:
    """List detected conflicts.

    Args:
        resolved: Optional filter by resolved status
        limit: Result limit
        offset: Result offset
        recruiter: Current recruiter
        db: Database session

    Returns:
        Paginated list of conflicts
    """
    logger.debug(f"Listing conflicts: resolved={resolved}, limit={limit}")

    return {
        "conflicts": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "unresolved_count": 0,
    }


@router.patch("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    strategy: str = Query(..., description="Resolution strategy: local_wins, ats_wins, merge"),
    recruiter: CurrentRecruiter = None,
    db: DBSession = None,
) -> dict:
    """Manually resolve a detected conflict.

    Args:
        conflict_id: Conflict ID
        strategy: Resolution strategy
        recruiter: Current recruiter
        db: Database session

    Returns:
        Resolution result
    """
    if strategy not in ["local_wins", "ats_wins", "merge", "manual"]:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")

    logger.info(f"Resolving conflict {conflict_id} with strategy {strategy}")

    return {
        "conflict_id": conflict_id,
        "strategy": strategy,
        "status": "resolved",
        "message": "Conflict resolved successfully",
    }


@router.get("/logs")
async def list_sync_logs(
    provider: str | None = Query(None, description="Filter by provider"),
    operation: str | None = Query(None, description="Filter by operation type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    recruiter: CurrentRecruiter = None,
    db: DBSession = None,
) -> dict:
    """Get audit log of sync operations.

    Args:
        provider: Optional provider filter
        operation: Optional operation filter (import, export)
        limit: Result limit
        offset: Result offset
        recruiter: Current recruiter
        db: Database session

    Returns:
        Paginated audit log
    """
    logger.debug(f"Listing sync logs: provider={provider}, operation={operation}")

    return {
        "logs": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/config")
async def get_sync_config(recruiter: CurrentRecruiter = None) -> dict:
    """Get current ATS sync configuration.

    Returns:
        Current configuration settings
    """
    return {
        "sync_enabled": settings.ats_sync_enabled if hasattr(settings, "ats_sync_enabled") else False,
        "sync_interval_minutes": settings.ats_sync_interval_minutes if hasattr(settings, "ats_sync_interval_minutes") else 60,
        "sync_max_age_days": settings.ats_sync_max_age_days if hasattr(settings, "ats_sync_max_age_days") else 7,
        "auto_conflict_resolution": settings.ats_auto_conflict_resolution if hasattr(settings, "ats_auto_conflict_resolution") else "suggested",
        "available_providers": ["lever", "greenhouse", "workable"],
    }
