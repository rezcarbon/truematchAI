"""Job management endpoints for candidates and recruiters."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, and_, func, or_
from pydantic import BaseModel

from app.deps import CurrentUser, DBSession
from app.models.position import Position, PositionStatus
from app.models.saved_job import SavedJob
from app.core.clock import utcnow
from app.core.exceptions import NotFoundError, AuthorizationError

logger = logging.getLogger("truematch.jobs")

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreate(BaseModel):
    """Create a new job posting."""
    title: str
    company: str
    location: Optional[str] = None
    description: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = None
    requirements: Optional[dict] = None


class JobResponse(BaseModel):
    """Job response schema."""
    id: uuid.UUID
    title: str
    description: str
    company: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = None
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """List of jobs."""
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    user: CurrentUser = None,
    db: DBSession = None,
) -> Position:
    """Create a new job posting (recruiter only)."""
    if user.role.value not in ("recruiter", "admin"):
        raise AuthorizationError("Only recruiters can create jobs")

    position = Position(
        title=payload.title,
        description=payload.description,
        status=PositionStatus.open,
        created_by=user.id,
        company_id=None,  # TODO: link to company when company management is added
        parsed_requirements=payload.requirements or {},
    )

    # Store additional fields as supplementary data
    position.supplementary = {
        "company": payload.company,
        "location": payload.location,
        "salary_min": payload.salary_min,
        "salary_max": payload.salary_max,
        "job_type": payload.job_type,
    }

    db.add(position)
    await db.commit()
    logger.info(f"Job created: {position.id} by user {user.id}")
    return position


@router.get("", response_model=JobListResponse)
async def list_jobs(
    search: Optional[str] = Query(None, description="Search in title and description"),
    location: Optional[str] = Query(None, description="Filter by location"),
    status_filter: Optional[str] = Query(None, description="Filter by status (open, closed, archived)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = None,
    db: DBSession = None,
) -> JobListResponse:
    """List jobs with optional filtering and search."""
    stmt = select(Position)

    # Filter by status
    if status_filter:
        try:
            status_enum = PositionStatus[status_filter.lower()]
            stmt = stmt.where(Position.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    # Search filter
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Position.title.ilike(search_term),
                Position.description.ilike(search_term),
            )
        )

    # Location filter (from supplementary data)
    # For simple implementation, we'll filter after fetching
    # In production, this should be indexed

    # Count total
    count_stmt = select(func.count()).select_from(Position).where(stmt.whereclause)
    total = await db.scalar(count_stmt) or 0

    # Pagination
    stmt = (
        stmt.order_by(Position.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    jobs = list((await db.scalars(stmt)).all())

    # Filter by location if needed (post-fetch)
    if location:
        jobs = [
            j for j in jobs
            if j.supplementary and j.supplementary.get("location", "").lower() == location.lower()
        ]

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> Position:
    """Get a specific job posting."""
    job = await db.get(Position, job_id)
    if not job:
        raise NotFoundError("Job not found")
    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: uuid.UUID,
    payload: JobCreate,
    user: CurrentUser = None,
    db: DBSession = None,
) -> Position:
    """Update a job posting (creator or admin only)."""
    job = await db.get(Position, job_id)
    if not job:
        raise NotFoundError("Job not found")

    if user.role.value not in ("admin",) and job.created_by != user.id:
        raise AuthorizationError("Not authorized to update this job")

    job.title = payload.title
    job.description = payload.description
    job.updated_at = utcnow()
    job.supplementary = {
        "company": payload.company,
        "location": payload.location,
        "salary_min": payload.salary_min,
        "salary_max": payload.salary_max,
        "job_type": payload.job_type,
    }

    await db.commit()
    logger.info(f"Job updated: {job.id} by user {user.id}")
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> None:
    """Delete a job posting (creator or admin only)."""
    job = await db.get(Position, job_id)
    if not job:
        raise NotFoundError("Job not found")

    if user.role.value not in ("admin",) and job.created_by != user.id:
        raise AuthorizationError("Not authorized to delete this job")

    await db.delete(job)
    await db.commit()
    logger.info(f"Job deleted: {job.id} by user {user.id}")


@router.post("/{job_id}/save", status_code=status.HTTP_201_CREATED)
async def save_job(
    job_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> dict:
    """Save a job for later (candidate only)."""
    job = await db.get(Position, job_id)
    if not job:
        raise NotFoundError("Job not found")

    # Check if already saved
    existing = await db.execute(
        select(SavedJob).where(
            and_(SavedJob.user_id == user.id, SavedJob.position_id == job_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job already saved",
        )

    saved = SavedJob(
        user_id=user.id,
        position_id=job_id,
        created_at=utcnow(),
    )
    db.add(saved)
    await db.commit()
    return {"saved": True, "job_id": str(job_id)}


@router.delete("/{job_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    job_id: uuid.UUID,
    user: CurrentUser = None,
    db: DBSession = None,
) -> None:
    """Remove a job from saved (candidate only)."""
    saved = await db.execute(
        select(SavedJob).where(
            and_(SavedJob.user_id == user.id, SavedJob.position_id == job_id)
        )
    )
    saved_job = saved.scalar_one_or_none()
    if not saved_job:
        raise NotFoundError("Saved job not found")

    await db.delete(saved_job)
    await db.commit()
