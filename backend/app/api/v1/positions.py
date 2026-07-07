"""Position endpoints."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, func, select, or_
from sqlalchemy.orm import selectinload

from app.config import settings
from app.deps import CurrentUser, DBSession
from app.engines import corpus, jd_evolution, reasoning
from app.engines.intake import analyze_jd
from app.models.jd_version import JDVersion
from app.models.position import Position
from app.models.user import UserRole
from app.models.saved_job import SavedJob, SavedJobStatus
from app.models.application import Application, PipelineStage
from app.schemas.position import (
    PositionCreate,
    PositionList,
    PositionResponse,
    PositionUpdate,
)
from app.schemas.job_search import (
    JobSearchResults,
    JobSearchResponse,
    SaveJobRequest,
    SaveJobResponse,
    SavedJobsList,
    ApplicationRequest,
    ApplicationResponse,
)
from app.core.clock import utcnow

router = APIRouter()
logger = logging.getLogger("truematch.positions")


def _require_recruiter(user: CurrentUser) -> None:
    if user.role not in (UserRole.recruiter, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter role required"
        )


async def _snapshot_jd(db: DBSession, position: Position) -> None:
    """Append an immutable JD version snapshot (Pillar 3 history + audit record)."""
    count = await db.scalar(
        select(func.count()).select_from(JDVersion).where(JDVersion.position_id == position.id)
    )
    db.add(
        JDVersion(
            position_id=position.id,
            version=(count or 0) + 1,
            description=position.description,
            parsed_requirements=position.parsed_requirements,
            jd_quality_score=position.jd_quality_score,
            jd_issues=position.jd_issues,
        )
    )
    await db.flush()


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    payload: PositionCreate, user: CurrentUser, db: DBSession
) -> Position:
    _require_recruiter(user)
    company_id = payload.company_id or user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="company_id required (user has no company)",
        )

    # Synchronous JD analysis + interrogation for immediate quality feedback.
    requirements = analyze_jd(payload.description or "")
    jd_review = reasoning.interrogate_jd(payload.description or "")

    position = Position(
        company_id=company_id,
        created_by=user.id,
        title=payload.title,
        description=payload.description,
        parsed_requirements=requirements,
        jd_quality_score=jd_review.get("quality_score"),
        jd_issues={"issues": jd_review.get("issues", [])},
    )
    db.add(position)
    await db.flush()
    await _snapshot_jd(db, position)  # version 1
    await corpus.record_jd(db, position.description or "")  # corpus learning
    return position


@router.get("", response_model=PositionList)
async def list_positions(user: CurrentUser, db: DBSession) -> PositionList:
    stmt = select(Position)
    count_stmt = select(func.count()).select_from(Position)
    if user.company_id is not None:
        stmt = stmt.where(Position.company_id == user.company_id)
        count_stmt = count_stmt.where(Position.company_id == user.company_id)
    total = await db.scalar(count_stmt) or 0
    items = list((await db.scalars(stmt.order_by(Position.created_at.desc()))).all())
    return PositionList(
        items=[PositionResponse.model_validate(p) for p in items], total=total
    )


@router.get("/taxonomy")
async def get_role_taxonomy(user: CurrentUser, db: DBSession) -> dict:
    """The self-learned role taxonomy: clusters (role families) + members.

    Declared before /{position_id} so 'taxonomy' is not parsed as a UUID.
    """
    from app.models.role_cluster import RoleCluster

    clusters = list(
        (await db.scalars(select(RoleCluster).order_by(RoleCluster.size.desc()))).all()
    )
    out = []
    for c in clusters:
        members = list(
            (
                await db.scalars(
                    select(Position).where(Position.role_cluster_id == c.id)
                )
            ).all()
        )
        out.append(
            {
                "id": str(c.id),
                "label": c.label,
                "size": c.size,
                "top_capabilities": c.top_capabilities or [],
                "method": c.method,
                "members": [{"id": str(p.id), "title": p.title} for p in members],
            }
        )
    return {"clusters": out, "total": len(out)}


@router.post("/taxonomy/rebuild")
async def rebuild_role_taxonomy_endpoint(user: CurrentUser, db: DBSession) -> dict:
    """Trigger a recompute of the role taxonomy (recruiter/admin)."""
    _require_recruiter(user)
    try:
        from app.workers.tasks import rebuild_role_taxonomy

        rebuild_role_taxonomy.delay()
        return {"status": "queued"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not enqueue taxonomy rebuild: %s", exc)
        raise HTTPException(status_code=503, detail="Could not enqueue rebuild") from exc


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> Position:
    position = await db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    return position


@router.patch("/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: uuid.UUID, payload: PositionUpdate, user: CurrentUser, db: DBSession
) -> Position:
    _require_recruiter(user)
    position = await db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(position, key, value)
    # A description change re-runs JD analysis and snapshots a new version so the
    # evolution engine has a longitudinal record.
    if "description" in data:
        requirements = analyze_jd(position.description or "")
        jd_review = reasoning.interrogate_jd(position.description or "")
        position.parsed_requirements = requirements
        position.jd_quality_score = jd_review.get("quality_score")
        position.jd_issues = {"issues": jd_review.get("issues", [])}
        await db.flush()
        await _snapshot_jd(db, position)
        await corpus.record_jd(db, position.description or "")  # corpus learning
        # Auto-rescore: if this JD edit drifted, re-run assessments for the
        # position's candidates. The task recomputes drift deterministically
        # and no-ops when there are no drift signals; commit first so it sees
        # the new version row.
        if settings.auto_rescore_on_drift:
            # Commit so the worker (separate connection) sees the new JD
            # version, then refresh so the response model can still serialize
            # the (otherwise expired) position attributes.
            await db.commit()
            await db.refresh(position)
            try:
                from app.workers.tasks import rescore_position_on_drift

                rescore_position_on_drift.delay(str(position.id))
            except Exception:  # noqa: BLE001 — broker hiccup must not fail the edit
                logger.warning("Could not enqueue drift rescore for %s", position.id)
    else:
        await db.flush()
    return position


@router.get("/{position_id}/jd-versions")
async def list_jd_versions(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    """Immutable JD version history for a position (Pillar 3 + audit record)."""
    versions = list(
        (
            await db.scalars(
                select(JDVersion)
                .where(JDVersion.position_id == position_id)
                .order_by(JDVersion.version)
            )
        ).all()
    )
    return {
        "position_id": str(position_id),
        "versions": [
            {
                "version": v.version,
                "jd_quality_score": v.jd_quality_score,
                "parsed_requirements": v.parsed_requirements,
                "jd_issues": v.jd_issues,
                "created_at": v.created_at,
            }
            for v in versions
        ],
    }


@router.get("/{position_id}/evolution")
async def get_jd_evolution(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    """How the role's JD has evolved + how it should evolve next (Pillar 3)."""
    versions = list(
        (
            await db.scalars(
                select(JDVersion)
                .where(JDVersion.position_id == position_id)
                .order_by(JDVersion.version)
            )
        ).all()
    )
    history = [
        {
            "version": v.version,
            "description": v.description,
            "parsed_requirements": v.parsed_requirements,
            "jd_quality_score": v.jd_quality_score,
            "jd_issues": v.jd_issues,
        }
        for v in versions
    ]
    return jd_evolution.analyze_evolution(history)


@router.get("", response_model=JobSearchResults)
async def search_positions(
    user: CurrentUser,
    db: DBSession,
    filters_role: str | None = Query(None, alias="filters[role]"),
    filters_location: str | None = Query(None, alias="filters[location]"),
    filters_match_score: str | None = Query(None, alias="filters[match_score]"),
    filters_company: str | None = Query(None, alias="filters[company]"),
    filters_salary_min: int | None = Query(None, alias="filters[salary_min]", ge=0),
    filters_salary_max: int | None = Query(None, alias="filters[salary_max]", ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> JobSearchResults:
    """Search jobs with capability matching and filtering.

    Supports filtering by role, location, salary, match score, and company.
    Returns jobs with calculated match scores for the current user.
    """
    stmt = select(Position).where(Position.status == "open")
    count_stmt = select(func.count()).select_from(Position).where(Position.status == "open")

    # Apply filters
    filters = []

    if filters_role:
        filters.append(Position.title.ilike(f"%{filters_role}%"))

    if filters_location:
        filters.append(Position.description.ilike(f"%{filters_location}%"))

    if filters_company and user.company_id:
        filters.append(Position.company_id == user.company_id)

    if filters:
        stmt = stmt.where(or_(*filters))
        count_stmt = count_stmt.where(or_(*filters))

    # Get total count before pagination
    total = await db.scalar(count_stmt) or 0

    # Apply pagination
    stmt = (
        stmt.order_by(Position.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    positions = list((await db.scalars(stmt)).all())

    # Build response with match score calculation
    items = []
    for position in positions:
        match_score = None
        capability_gap_areas = None

        # Calculate match score based on candidate's assessments
        # This is a placeholder - implement actual capability matching logic
        if user.role == UserRole.candidate:
            # Find recent assessments for this position
            from app.models.assessment import Assessment

            recent_assessment = await db.scalar(
                select(Assessment)
                .where(
                    and_(
                        Assessment.position_id == position.id,
                        Assessment.user_id == user.id,
                    )
                )
                .order_by(Assessment.created_at.desc())
                .limit(1)
            )

            if recent_assessment and recent_assessment.capability_score:
                match_score = recent_assessment.capability_score
                capability_gap_areas = recent_assessment.counter_rec_evidence.get(
                    "gap_areas", []
                ) if recent_assessment.counter_rec_evidence else None

        items.append(
            JobSearchResponse(
                id=position.id,
                title=position.title,
                description=position.description,
                company_id=position.company_id,
                status=position.status.value,
                parsed_requirements=position.parsed_requirements,
                jd_quality_score=position.jd_quality_score,
                match_score=match_score,
                capability_gap_areas=capability_gap_areas,
                created_at=position.created_at,
                updated_at=position.updated_at,
            )
        )

    # Filter by match_score range if specified
    if filters_match_score:
        items = _filter_by_match_score(items, filters_match_score)

    return JobSearchResults(items=items, total=total, page=page, page_size=page_size)


def _filter_by_match_score(items: list, match_score_range: str) -> list:
    """Filter items by match score range.

    Supports formats: '80-100', '80', '>=80', '<=100'
    """
    if "-" in match_score_range:
        min_val, max_val = map(int, match_score_range.split("-"))
        return [
            i for i in items
            if i.match_score and min_val <= i.match_score <= max_val
        ]
    elif match_score_range.startswith(">="):
        threshold = int(match_score_range[2:])
        return [i for i in items if i.match_score and i.match_score >= threshold]
    elif match_score_range.startswith("<="):
        threshold = int(match_score_range[2:])
        return [i for i in items if i.match_score and i.match_score <= threshold]
    else:
        threshold = int(match_score_range)
        return [i for i in items if i.match_score and i.match_score == threshold]


@router.post("/candidate/saved-jobs", response_model=SaveJobResponse, status_code=status.HTTP_201_CREATED)
async def save_job(
    payload: SaveJobRequest,
    user: CurrentUser,
    db: DBSession,
) -> SaveJobResponse:
    """Save a job for later review.

    Creates or updates a saved job record for the current candidate user.
    Enforces candidate role and ownership.
    """
    if user.role != UserRole.candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can save jobs",
        )

    # Verify position exists
    position = await db.get(Position, payload.position_id)
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    # Check if already saved
    existing = await db.scalar(
        select(SavedJob).where(
            and_(
                SavedJob.user_id == user.id,
                SavedJob.position_id == payload.position_id,
            )
        )
    )

    if existing:
        # Update existing
        existing.list_name = payload.list_name
        existing.notes = payload.notes
        existing.updated_at = utcnow()
        if existing.status == SavedJobStatus.archived:
            existing.status = SavedJobStatus.saved
            existing.archived_at = None
        await db.flush()
        return SaveJobResponse.model_validate(existing)

    # Create new
    saved_job = SavedJob(
        user_id=user.id,
        position_id=payload.position_id,
        job_title=position.title,
        company_name=None,  # Extract from company model if needed
        list_name=payload.list_name,
        notes=payload.notes,
        status=SavedJobStatus.saved,
        notify_on_update=True,
    )

    db.add(saved_job)
    await db.flush()

    logger.info(
        "Job saved",
        extra={"user_id": str(user.id), "position_id": str(payload.position_id)},
    )

    return SaveJobResponse.model_validate(saved_job)


@router.get("/candidate/saved-jobs", response_model=SavedJobsList)
async def list_saved_jobs(
    user: CurrentUser,
    db: DBSession,
    status_filter: str | None = Query(None, alias="status"),
    list_name: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> SavedJobsList:
    """List saved jobs for the current candidate.

    Supports filtering by status and list name. Returns paginated results
    with position metadata and match scores.
    """
    if user.role != UserRole.candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can view saved jobs",
        )

    stmt = select(SavedJob).where(SavedJob.user_id == user.id)
    count_stmt = select(func.count()).select_from(SavedJob).where(SavedJob.user_id == user.id)

    # Filter by status
    if status_filter:
        stmt = stmt.where(SavedJob.status == status_filter)
        count_stmt = count_stmt.where(SavedJob.status == status_filter)
    else:
        # Exclude archived by default
        stmt = stmt.where(SavedJob.status != SavedJobStatus.archived)
        count_stmt = count_stmt.where(SavedJob.status != SavedJobStatus.archived)

    # Filter by list name
    if list_name:
        stmt = stmt.where(SavedJob.list_name == list_name)
        count_stmt = count_stmt.where(SavedJob.list_name == list_name)

    # Get total
    total = await db.scalar(count_stmt) or 0

    # Apply pagination
    stmt = (
        stmt.order_by(SavedJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    saved_jobs = list((await db.scalars(stmt)).all())

    items = [SaveJobResponse.model_validate(job) for job in saved_jobs]

    logger.info(
        "Listed saved jobs",
        extra={"user_id": str(user.id), "total": total},
    )

    return SavedJobsList(items=items, total=total, page=page, page_size=page_size)


@router.delete("/candidate/saved-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved_job(
    job_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Remove a job from saved jobs.

    Soft-deletes by marking as archived. Enforces ownership.
    """
    if user.role != UserRole.candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can manage saved jobs",
        )

    saved_job = await db.get(SavedJob, job_id)
    if saved_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found",
        )

    if saved_job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own saved jobs",
        )

    # Soft delete
    saved_job.status = SavedJobStatus.archived
    saved_job.archived_at = utcnow()
    saved_job.updated_at = utcnow()
    await db.flush()

    logger.info(
        "Saved job removed",
        extra={"user_id": str(user.id), "job_id": str(job_id)},
    )

    return None


@router.post("/{position_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_position(
    position_id: uuid.UUID,
    payload: ApplicationRequest,
    user: CurrentUser,
    db: DBSession,
) -> ApplicationResponse:
    """Apply to a position as a candidate.

    Creates an Application record and optionally saves the job.
    Requires candidate role and a valid resume.
    """
    if user.role != UserRole.candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can apply to positions",
        )

    # Verify position exists
    position = await db.get(Position, position_id)
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )

    # Verify resume exists and belongs to user
    from app.models.resume import Resume

    resume = await db.get(Resume, payload.resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to user",
        )

    # Check if already applied
    existing_application = await db.scalar(
        select(Application).where(
            and_(
                Application.user_id == user.id,
                Application.position_id == position_id,
                Application.resume_id == payload.resume_id,
            )
        )
    )

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this position",
        )

    # Create application
    application = Application(
        user_id=user.id,
        position_id=position_id,
        resume_id=payload.resume_id,
        stage=PipelineStage.applied,
        source=payload.source,
        applied_at=utcnow(),
    )

    db.add(application)
    await db.flush()

    # Auto-save the job if not already saved
    try:
        existing_save = await db.scalar(
            select(SavedJob).where(
                and_(
                    SavedJob.user_id == user.id,
                    SavedJob.position_id == position_id,
                )
            )
        )
        if not existing_save:
            saved_job = SavedJob(
                user_id=user.id,
                position_id=position_id,
                job_title=position.title,
                status=SavedJobStatus.applied,
                applied_at=utcnow(),
            )
            db.add(saved_job)
            await db.flush()
    except Exception as e:
        logger.warning(
            "Could not auto-save job on application",
            extra={"error": str(e), "position_id": str(position_id)},
        )

    logger.info(
        "Application created",
        extra={
            "user_id": str(user.id),
            "position_id": str(position_id),
            "application_id": str(application.id),
        },
    )

    return ApplicationResponse.model_validate(application)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> None:
    _require_recruiter(user)
    position = await db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    await db.delete(position)
    return None
