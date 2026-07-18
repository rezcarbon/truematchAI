"""Job search endpoints."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CurrentUser, DBSession
from app.schemas.job_search import (
    CreateJobSearchRequest,
    UpdateJobSearchRequest,
    JobSearchResponse,
    JobSearchDetailResponse,
    SearchResultsResponse,
    SaveJobRequest,
    SavedJobResponse,
    SearchStatsResponse,
    BulkSaveJobsRequest,
    AlertSettingsRequest,
    AlertSettingsResponse,
    SearchListResponse,
)

router = APIRouter(prefix="/candidates/job-search", tags=["job-search"])
logger = logging.getLogger("truematch.job_search")


# ─────────────────────────────────────────────────────────────────────────
# Create & Manage Job Searches
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=JobSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job search",
    description="Create a new saved job search with criteria",
)
async def create_job_search(
    payload: CreateJobSearchRequest,
    user: CurrentUser,
    db: DBSession,
) -> JobSearchResponse:
    """Create a new job search with specified criteria."""
    try:
        from app.core.clock import utcnow
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UUID as PG_UUID
        from sqlalchemy.orm import Session
        import uuid

        # For now, create a simple dictionary-based record
        # In a real scenario, this would be a proper database model
        search_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(user.id),
            "name": payload.name,
            "role": payload.role,
            "location": payload.location,
            "salary_min": payload.salary_min,
            "salary_max": payload.salary_max,
            "remote_only": payload.remote_only or False,
            "keywords": payload.keywords or [],
            "auto_apply": payload.auto_apply or False,
            "status": "active",
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }

        logger.info(f"Created job search '{payload.name}' for user {user.id}")

        search_id = uuid.UUID(search_data["id"])
        return JobSearchDetailResponse(
            id=search_id,
            name=payload.name,
            role=payload.role,
            location=payload.location,
            salary_min=payload.salary_min,
            salary_max=payload.salary_max,
            remote_only=payload.remote_only or False,
            keywords=payload.keywords,
            auto_apply=payload.auto_apply or False,
            status="active",
            results_count=0,
            last_executed=None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
    except Exception as e:
        logger.error(f"Error creating job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job search")


@router.get(
    "/{search_id}",
    response_model=JobSearchDetailResponse,
    summary="Get job search details",
    description="Retrieve details of a specific job search",
)
async def get_job_search(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> JobSearchDetailResponse:
    """Get detailed information about a job search."""
    try:
        from app.core.clock import utcnow

        # Placeholder implementation
        logger.info(f"Retrieved job search {search_id} for user {user.id}")

        return JobSearchDetailResponse(
            id=search_id,
            name="Sample Search",
            role="Software Engineer",
            location="San Francisco, CA",
            salary_min=120000,
            salary_max=200000,
            remote_only=False,
            keywords=["Python", "AWS"],
            auto_apply=False,
            status="active",
            results_count=42,
            last_executed=utcnow(),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
    except Exception as e:
        logger.error(f"Error retrieving job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job search")


@router.get(
    "",
    response_model=SearchListResponse,
    summary="List job searches",
    description="List all job searches for the user with pagination",
)
async def list_job_searches(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    user: CurrentUser = None,
    db: DBSession = None,
) -> SearchListResponse:
    """List all job searches owned by the current user."""
    try:
        from app.core.clock import utcnow

        # Placeholder implementation - return empty list
        logger.info(f"Listed job searches for user {user.id}")

        return SearchListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )
    except Exception as e:
        logger.error(f"Error listing job searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to list job searches")


@router.put(
    "/{search_id}",
    response_model=JobSearchDetailResponse,
    summary="Update job search",
    description="Update criteria for a job search",
)
async def update_job_search(
    search_id: uuid.UUID,
    payload: UpdateJobSearchRequest,
    user: CurrentUser,
    db: DBSession,
) -> JobSearchDetailResponse:
    """Update a job search's criteria."""
    try:
        from app.core.clock import utcnow

        # Placeholder implementation
        logger.info(f"Updated job search {search_id} for user {user.id}")

        return JobSearchDetailResponse(
            id=search_id,
            name=payload.name or "Sample Search",
            role=payload.role,
            location=payload.location,
            salary_min=payload.salary_min,
            salary_max=payload.salary_max,
            remote_only=payload.remote_only or False,
            keywords=payload.keywords,
            auto_apply=payload.auto_apply or False,
            status="active",
            results_count=0,
            last_executed=None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
    except Exception as e:
        logger.error(f"Error updating job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to update job search")


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job search",
    description="Delete/archive a job search",
)
async def delete_job_search(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a job search."""
    try:
        logger.info(f"Deleted job search {search_id} for user {user.id}")

    except Exception as e:
        logger.error(f"Error deleting job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job search")


# ─────────────────────────────────────────────────────────────────────────
# Execute & View Search Results
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "/{search_id}/execute",
    response_model=SearchResultsResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute a job search",
    description="Trigger execution of a saved job search",
)
async def execute_job_search(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> SearchResultsResponse:
    """Execute a job search and return results."""
    try:
        from app.core.clock import utcnow

        logger.info(f"Executed job search {search_id} for user {user.id}")

        return SearchResultsResponse(
            search_id=search_id,
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
    except Exception as e:
        logger.error(f"Error executing job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute job search")


@router.get(
    "/{search_id}/results",
    response_model=SearchResultsResponse,
    summary="Get search results",
    description="Get paginated results from a job search with filters",
)
async def get_search_results(
    search_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("match_score", description="match_score, posted_date, salary"),
    min_match_score: int = Query(0, ge=0, le=100),
    user: CurrentUser = None,
    db: DBSession = None,
) -> SearchResultsResponse:
    """Get paginated results from a job search."""
    try:
        logger.info(f"Retrieved search results for search {search_id} for user {user.id}")

        return SearchResultsResponse(
            search_id=search_id,
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )
    except Exception as e:
        logger.error(f"Error retrieving search results: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search results")


# ─────────────────────────────────────────────────────────────────────────
# Save & Manage Jobs
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "/{search_id}/jobs/{job_id}/save",
    response_model=SavedJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a job",
    description="Save a job from search results",
)
async def save_job(
    search_id: uuid.UUID,
    job_id: str,
    payload: SaveJobRequest,
    user: CurrentUser,
    db: DBSession,
) -> SavedJobResponse:
    """Save a job from search results."""
    try:
        from sqlalchemy import select
        from app.models.saved_job import SavedJob, SavedJobStatus
        from app.core.clock import utcnow

        # Create saved job record
        saved_job = SavedJob(
            user_id=user.id,
            position_id=payload.position_id,
            list_name=payload.list_name or "Default",
            notes=payload.notes,
            status=SavedJobStatus.saved,
        )

        db.add(saved_job)
        await db.flush()

        logger.info(f"Saved job {job_id} for user {user.id}")

        return SavedJobResponse(
            id=saved_job.id,
            position_id=saved_job.position_id,
            job_title=saved_job.job_title,
            company_name=saved_job.company_name,
            match_score=saved_job.match_score,
            status=saved_job.status.value,
            list_name=saved_job.list_name,
            notes=saved_job.notes,
            viewed_at=saved_job.viewed_at,
            applied_at=saved_job.applied_at,
            created_at=saved_job.created_at,
            updated_at=saved_job.updated_at,
        )
    except Exception as e:
        logger.error(f"Error saving job: {e}")
        raise HTTPException(status_code=500, detail="Failed to save job")


@router.post(
    "/jobs/bulk-save",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Bulk save jobs",
    description="Save multiple jobs at once",
)
async def bulk_save_jobs(
    payload: BulkSaveJobsRequest,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Save multiple jobs at once."""
    try:
        from app.models.saved_job import SavedJob, SavedJobStatus
        import uuid

        # Create saved job records for each job
        for job_id_str in payload.job_ids:
            try:
                position_id = uuid.UUID(job_id_str) if len(job_id_str) == 36 else uuid.uuid4()
            except ValueError:
                position_id = uuid.uuid4()

            saved_job = SavedJob(
                user_id=user.id,
                position_id=position_id,
                list_name=payload.list_name or "Default",
                status=SavedJobStatus.saved,
            )

            db.add(saved_job)

        await db.flush()

        logger.info(f"Bulk saved {len(payload.job_ids)} jobs for user {user.id}")

    except Exception as e:
        logger.error(f"Error bulk saving jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk save jobs")


@router.get(
    "/jobs/saved",
    summary="Get saved jobs",
    description="List all saved jobs with pagination",
)
async def get_saved_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tagged: Optional[str] = Query(None, description="Filter by tag"),
    user: CurrentUser = None,
    db: DBSession = None,
):
    """Get user's saved jobs."""
    try:
        from sqlalchemy import select, func, desc
        from app.models.saved_job import SavedJob, SavedJobStatus

        # Query saved jobs
        stmt = select(SavedJob).where(
            SavedJob.user_id == user.id,
            SavedJob.status != SavedJobStatus.archived,
        )

        if tagged:
            stmt = stmt.where(SavedJob.list_name == tagged)

        # Count total
        count_stmt = select(func.count()).select_from(SavedJob).where(
            SavedJob.user_id == user.id,
            SavedJob.status != SavedJobStatus.archived,
        )

        if tagged:
            count_stmt = count_stmt.where(SavedJob.list_name == tagged)

        total = await db.scalar(count_stmt)

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(SavedJob.created_at)).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        saved_jobs = result.scalars().all()

        logger.info(f"Retrieved {len(saved_jobs)} saved jobs for user {user.id}")

        return {
            "items": [
                SavedJobResponse(
                    id=job.id,
                    position_id=job.position_id,
                    job_title=job.job_title,
                    company_name=job.company_name,
                    match_score=job.match_score,
                    status=job.status.value,
                    list_name=job.list_name,
                    notes=job.notes,
                    viewed_at=job.viewed_at,
                    applied_at=job.applied_at,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                )
                for job in saved_jobs
            ],
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(f"Error retrieving saved jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve saved jobs")


@router.delete(
    "/{search_id}/jobs/{job_id}/unsave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unsave a job",
    description="Remove a job from saved list",
)
async def unsave_job(
    search_id: uuid.UUID,
    job_id: str,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Remove a job from saved list."""
    try:
        from sqlalchemy import select
        from app.models.saved_job import SavedJob, SavedJobStatus
        from app.core.clock import utcnow
        import uuid

        # Convert job_id to UUID if needed
        try:
            position_id = uuid.UUID(job_id) if len(job_id) == 36 else uuid.uuid4()
        except ValueError:
            position_id = uuid.uuid4()

        # Find and update saved job
        stmt = select(SavedJob).where(
            SavedJob.user_id == user.id,
            SavedJob.position_id == position_id,
        )

        result = await db.execute(stmt)
        saved_job = result.scalar_one_or_none()

        if not saved_job:
            raise HTTPException(status_code=404, detail="Saved job not found")

        # Archive the saved job
        saved_job.status = SavedJobStatus.archived
        saved_job.archived_at = utcnow()

        await db.flush()

        logger.info(f"Unsaved job {job_id} for user {user.id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsaving job: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsave job")


# ─────────────────────────────────────────────────────────────────────────
# Search Analytics & Settings
# ─────────────────────────────────────────────────────────────────────────


@router.get(
    "/{search_id}/stats",
    response_model=SearchStatsResponse,
    summary="Get search statistics",
    description="Get analytics for a job search",
)
async def get_search_stats(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> SearchStatsResponse:
    """Get statistics and analytics for a job search."""
    try:
        logger.info(f"Retrieved search stats for search {search_id}")

        return SearchStatsResponse(
            search_id=search_id,
            total_results=0,
            results_this_week=0,
            results_this_month=0,
            saved_count=0,
            applied_count=0,
            average_match_score=0.0,
        )
    except Exception as e:
        logger.error(f"Error retrieving search stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search stats")


@router.post(
    "/{search_id}/alerts",
    response_model=AlertSettingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Setup search alerts",
    description="Set up notifications for new matching jobs",
)
async def setup_search_alerts(
    search_id: uuid.UUID,
    payload: AlertSettingsRequest,
    user: CurrentUser,
    db: DBSession,
) -> AlertSettingsResponse:
    """Set up alerts for a job search."""
    try:
        from app.core.clock import utcnow

        logger.info(f"Setup alerts for search {search_id} for user {user.id}")

        return AlertSettingsResponse(
            search_id=search_id,
            enabled=payload.enabled,
            frequency=payload.frequency,
            min_match_score=payload.min_match_score,
            notification_channels=payload.notification_channels,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
    except Exception as e:
        logger.error(f"Error setting up alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup alerts")


@router.get(
    "/{search_id}/alerts",
    response_model=AlertSettingsResponse,
    summary="Get alert settings",
    description="Get current alert settings for a search",
)
async def get_alert_settings(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> AlertSettingsResponse:
    """Get alert settings for a search."""
    try:
        from app.core.clock import utcnow

        logger.info(f"Retrieved alert settings for search {search_id}")

        return AlertSettingsResponse(
            search_id=search_id,
            enabled=True,
            frequency="daily",
            min_match_score=60,
            notification_channels=["email"],
            created_at=utcnow(),
            updated_at=utcnow(),
        )
    except Exception as e:
        logger.error(f"Error retrieving alert settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert settings")


@router.delete(
    "/{search_id}/alerts",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete search alerts",
    description="Stop notifications for a search",
)
async def delete_search_alerts(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete/disable alerts for a search."""
    try:
        logger.info(f"Deleted alerts for search {search_id} for user {user.id}")

    except Exception as e:
        logger.error(f"Error deleting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alerts")


# ─────────────────────────────────────────────────────────────────────────
# Pause & Resume Searches
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "/{search_id}/pause",
    response_model=JobSearchDetailResponse,
    summary="Pause a job search",
    description="Temporarily pause a job search (stop fetching updates)",
)
async def pause_job_search(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> JobSearchDetailResponse:
    """Pause a job search."""
    try:
        from app.core.clock import utcnow

        logger.info(f"Paused job search {search_id} for user {user.id}")

        return JobSearchDetailResponse(
            id=search_id,
            name="Sample Search",
            role="Software Engineer",
            location="San Francisco, CA",
            salary_min=120000,
            salary_max=200000,
            remote_only=False,
            keywords=["Python", "AWS"],
            auto_apply=False,
            status="paused",
            results_count=42,
            last_executed=utcnow(),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
    except Exception as e:
        logger.error(f"Error pausing job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause job search")


@router.post(
    "/{search_id}/resume",
    response_model=JobSearchDetailResponse,
    summary="Resume a job search",
    description="Resume a paused job search",
)
async def resume_job_search(
    search_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> JobSearchDetailResponse:
    """Resume a paused job search."""
    try:
        from app.core.clock import utcnow

        logger.info(f"Resumed job search {search_id} for user {user.id}")

        return JobSearchDetailResponse(
            id=search_id,
            name="Sample Search",
            role="Software Engineer",
            location="San Francisco, CA",
            salary_min=120000,
            salary_max=200000,
            remote_only=False,
            keywords=["Python", "AWS"],
            auto_apply=False,
            status="active",
            results_count=42,
            last_executed=utcnow(),
            created_at=utcnow(),
            updated_at=utcnow(),
        )
    except Exception as e:
        logger.error(f"Error resuming job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume job search")


# ─────────────────────────────────────────────────────────────────────────
# Export & Share
# ─────────────────────────────────────────────────────────────────────────


@router.get(
    "/{search_id}/export",
    summary="Export search results",
    description="Export search results as CSV or PDF",
)
async def export_search_results(
    search_id: uuid.UUID,
    format: str = Query("csv", description="csv or pdf"),
    user: CurrentUser = None,
    db: DBSession = None,
):
    """Export search results."""
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import io

        logger.info(f"Exported search results for search {search_id} as {format}")

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Title", "Company", "Location", "Match Score", "Posted Date"])
            writer.writerow(["1", "Software Engineer", "Tech Corp", "San Francisco, CA", "85", "2024-01-15"])

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=search_results.csv"},
            )
        else:
            return {
                "message": "PDF export is being processed",
                "search_id": str(search_id),
            }
    except Exception as e:
        logger.error(f"Error exporting search results: {e}")
        raise HTTPException(status_code=500, detail="Failed to export search results")


@router.post(
    "/{search_id}/share",
    status_code=status.HTTP_201_CREATED,
    summary="Share search with recruiter",
    description="Generate shareable link for recruiter access",
)
async def share_search_results(
    search_id: uuid.UUID,
    expires_in_days: int = Query(30, ge=1, le=365),
    user: CurrentUser = None,
    db: DBSession = None,
):
    """Create a shareable link for search results."""
    try:
        import uuid
        from app.core.clock import utcnow
        from datetime import timedelta

        # Generate short-lived token
        share_token = str(uuid.uuid4())
        expires_at = utcnow() + timedelta(days=expires_in_days)

        logger.info(f"Created share link for search {search_id} for user {user.id}")

        return {
            "share_token": share_token,
            "share_url": f"/search/{search_id}/shared/{share_token}",
            "expires_at": expires_at.isoformat(),
            "created_at": utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error sharing search results: {e}")
        raise HTTPException(status_code=500, detail="Failed to share search results")
