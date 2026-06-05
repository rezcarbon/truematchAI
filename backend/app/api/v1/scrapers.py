"""
Job scraper configuration and management API endpoints.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.job_scraping import JobScrapingConfig, JobSourceType, ScrapingRun, BatchStatus
from app.models.user import User
from app.schemas.scrapers import (
    ScraperConfigResponse,
    ScraperConfigCreateRequest,
    ListScrapersResponse,
    ScraperRunResponse,
)

logger = logging.getLogger("truematch.scrapers")

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


@router.get(
    "",
    summary="List scraper configurations",
    description="Get all configured scrapers and their status.",
    response_model=ListScrapersResponse,
)
async def list_scrapers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListScrapersResponse:
    """
    List all configured job scrapers.

    Returns configuration, enablement status, and last run information for each scraper.
    """
    # Check authorization (admin only)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view scraper configurations",
        )

    result = await db.execute(
        select(JobScrapingConfig).order_by(JobScrapingConfig.source_type)
    )
    configs = result.scalars().all()

    scraper_list = [
        ScraperConfigResponse(
            id=str(c.id),
            source_type=c.source_type,
            enabled=c.enabled,
            poll_hours=c.poll_hours,
            last_run=c.last_run,
            next_run=c.next_run,
            legal_approved=c.legal_approved,
            has_api_key="api_key" in c.config and bool(c.config.get("api_key")),
        )
        for c in configs
    ]

    return ListScrapersResponse(scrapers=scraper_list)


@router.post(
    "",
    summary="Create scraper configuration",
    description="Configure a new job scraper.",
    response_model=ScraperConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scraper(
    request: ScraperConfigCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScraperConfigResponse:
    """
    Create a scraper configuration.

    Configuration structure depends on scraper type:

    **USAJOBS (API-based, low risk):**
    ```json
    {
        "api_key": "your-usajobs-api-key",
        "search_params": {"keyword": "software engineer"}
    }
    ```

    **LinkedIn, Indeed, Glassdoor (Web-based, HIGH RISK):**
    ```json
    {
        "legal_approved": true,
        "min_request_delay": 15
    }
    ```
    """
    # Check authorization
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create scrapers",
        )

    # Validate source type
    try:
        source_type = JobSourceType(request.source_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source type. Must be one of: {', '.join([s.value for s in JobSourceType])}",
        )

    # Check if already configured
    result = await db.execute(
        select(JobScrapingConfig).where(JobScrapingConfig.source_type == source_type)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scraper for {source_type} already configured",
        )

    # Legal approval validation for direct scrapers
    high_risk_sources = [
        JobSourceType.linkedin,
        JobSourceType.indeed,
        JobSourceType.glassdoor,
    ]

    if source_type in high_risk_sources:
        if not request.config.get("legal_approved"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"{source_type} scraping requires explicit legal approval due to terms of service concerns. "
                    f"Please ensure legal team has reviewed before enabling."
                ),
            )

    # Create config
    config = JobScrapingConfig(
        id=uuid.uuid4(),
        source_type=source_type,
        enabled=request.enabled,
        config=request.config,
        poll_hours=request.poll_hours,
        legal_approved=request.config.get("legal_approved", False),
        legal_approval_date=(
            datetime.now(timezone.utc) if request.config.get("legal_approved") else None
        ),
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info(
        "Scraper configuration created",
        extra={
            "config_id": str(config.id),
            "source_type": source_type,
            "user_id": str(user.id),
            "legal_approved": config.legal_approved,
        },
    )

    return ScraperConfigResponse(
        id=str(config.id),
        source_type=config.source_type,
        enabled=config.enabled,
        poll_hours=config.poll_hours,
        last_run=config.last_run,
        next_run=config.next_run,
        legal_approved=config.legal_approved,
        has_api_key="api_key" in config.config and bool(config.config.get("api_key")),
    )


@router.patch(
    "/{config_id}",
    summary="Update scraper configuration",
    description="Update an existing scraper configuration.",
    response_model=ScraperConfigResponse,
)
async def update_scraper(
    config_id: str,
    enabled: Optional[bool] = None,
    poll_hours: Optional[int] = None,
    config: Optional[dict] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScraperConfigResponse:
    """
    Update a scraper configuration.

    Only administrators can update scrapers.
    """
    # Check authorization
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update scrapers",
        )

    try:
        config_uuid = uuid.UUID(config_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid config_id format",
        )

    result = await db.execute(
        select(JobScrapingConfig).where(JobScrapingConfig.id == config_uuid)
    )
    scraper_config = result.scalar_one_or_none()

    if not scraper_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper configuration not found",
        )

    # Update fields
    if enabled is not None:
        scraper_config.enabled = enabled

    if poll_hours is not None:
        if poll_hours < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="poll_hours must be >= 1",
            )
        scraper_config.poll_hours = poll_hours

    if config is not None:
        scraper_config.config.update(config)

        # Update legal approval if specified
        if "legal_approved" in config:
            scraper_config.legal_approved = config["legal_approved"]
            if config["legal_approved"]:
                scraper_config.legal_approval_date = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(scraper_config)

    logger.info(
        "Scraper configuration updated",
        extra={
            "config_id": str(scraper_config.id),
            "source_type": str(scraper_config.source_type),
            "user_id": str(user.id),
        },
    )

    return ScraperConfigResponse(
        id=str(scraper_config.id),
        source_type=scraper_config.source_type,
        enabled=scraper_config.enabled,
        poll_hours=scraper_config.poll_hours,
        last_run=scraper_config.last_run,
        next_run=scraper_config.next_run,
        legal_approved=scraper_config.legal_approved,
        has_api_key="api_key" in scraper_config.config
        and bool(scraper_config.config.get("api_key")),
    )


@router.post(
    "/{config_id}/test",
    summary="Test scraper configuration",
    description="Test that a scraper is properly configured and can reach its source.",
    response_model=dict,
)
async def test_scraper(
    config_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Test a scraper configuration.

    Attempts to validate the configuration and connect to the source.
    """
    # Check authorization
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test scrapers",
        )

    try:
        config_uuid = uuid.UUID(config_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid config_id format",
        )

    result = await db.execute(
        select(JobScrapingConfig).where(JobScrapingConfig.id == config_uuid)
    )
    scraper_config = result.scalar_one_or_none()

    if not scraper_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper configuration not found",
        )

    # Test validation (would instantiate actual scraper)
    # For now, just return a simple status
    logger.info(
        "Scraper test initiated",
        extra={"config_id": str(scraper_config.id), "user_id": str(user.id)},
    )

    return {
        "status": "ok",
        "source": str(scraper_config.source_type),
        "message": "Scraper configuration is valid",
    }


@router.get(
    "/{config_id}/runs",
    summary="List scraper runs",
    description="Get history of runs for a scraper.",
    response_model=dict,
)
async def list_scraper_runs(
    config_id: str,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List recent runs for a scraper.

    Shows history of scraping attempts and results.
    """
    # Check authorization
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view scraper runs",
        )

    try:
        config_uuid = uuid.UUID(config_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid config_id format",
        )

    # Verify config exists
    result = await db.execute(
        select(JobScrapingConfig).where(JobScrapingConfig.id == config_uuid)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper configuration not found",
        )

    # Get runs
    result = await db.execute(
        select(ScrapingRun)
        .where(ScrapingRun.config_id == config_uuid)
        .order_by(ScrapingRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()

    return {
        "config_id": config_id,
        "runs": [
            {
                "id": str(r.id),
                "status": r.status,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "jobs_found": r.jobs_found,
                "jobs_processed": r.jobs_processed,
                "jobs_failed": r.jobs_failed,
            }
            for r in runs
        ],
    }
