"""CV analysis endpoints for candidates."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, status
from sqlalchemy import select, func

from app.core.exceptions import NotFoundError
from app.deps import CurrentUser, DBSession
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisResult, CVAnalysisStatus
from app.models.position import Position
from app.models.resume import Resume
from app.schemas.cv_analysis import (
    CVAnalysisGapItem,
    CVAnalysisListItem,
    CVAnalysisRecommendation,
    CVAnalysisResult as CVAnalysisResultSchema,
    CVAnalysisStartRequest,
    CVAnalysisStartResponse,
    JobFitMatch,
    PaginatedCVAnalysisList,
)

router = APIRouter(prefix="/candidates/cv-analysis", tags=["cv-analysis"])
logger = logging.getLogger("truematch.cv_analysis")


@router.post(
    "",
    response_model=CVAnalysisStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start CV analysis",
    description="Initiate a CV analysis request. Returns 202 Accepted with analysis_id for polling.",
)
async def start_cv_analysis(
    payload: CVAnalysisStartRequest,
    user: CurrentUser,
    db: DBSession,
) -> CVAnalysisStartResponse:
    """Start a CV analysis for the candidate's resume.

    The analysis will be queued for async processing. Check the returned
    analysis_id to poll for results.
    """
    # Verify resume exists and belongs to user
    resume = await db.get(Resume, payload.resume_id)
    if resume is None or resume.user_id != user.id:
        raise NotFoundError(
            f"Resume {payload.resume_id} not found",
            instance="/api/v1/candidates/cv-analysis",
        )

    # Create analysis request
    analysis_req = CVAnalysisRequest(
        id=uuid.uuid4(),
        user_id=user.id,
        resume_id=payload.resume_id,
        target_role=payload.target_role,
        target_seniority=payload.target_seniority,
        career_focus_areas=payload.career_focus_areas,
    )
    db.add(analysis_req)
    await db.flush()

    logger.info(
        "CV analysis started",
        extra={
            "analysis_id": str(analysis_req.id),
            "user_id": str(user.id),
            "resume_id": str(payload.resume_id),
            "target_role": payload.target_role,
        },
    )

    # Commit the request first so it exists in the DB before the worker reads it
    await db.commit()

    # Enqueue the async task to the worker
    try:
        from app.workers.cv_analysis import process_cv_analysis_task
        process_cv_analysis_task.delay(str(analysis_req.id))
    except Exception as e:
        # In development, Celery may not be running. Log and continue.
        logger.warning(
            "Failed to enqueue CV analysis task - Celery may not be running",
            extra={"error": str(e), "analysis_id": str(analysis_req.id)},
        )

    return CVAnalysisStartResponse(
        analysis_id=analysis_req.id,
        status=analysis_req.status,
    )


@router.get(
    "/{analysis_id}",
    response_model=CVAnalysisResultSchema,
    summary="Get CV analysis results",
    description="Retrieve the results of a CV analysis request.",
)
async def get_cv_analysis(
    analysis_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> CVAnalysisResultSchema:
    """Get CV analysis results by ID.

    Returns analysis status and results once processing is complete.
    """
    # Get analysis request
    analysis_req = await db.get(CVAnalysisRequest, analysis_id)
    if analysis_req is None or analysis_req.user_id != user.id:
        raise NotFoundError(
            f"Analysis {analysis_id} not found",
            instance=f"/api/v1/candidates/cv-analysis/{analysis_id}",
        )

    # Get results if completed
    results = None
    if analysis_req.status == CVAnalysisStatus.completed:
        stmt = select(CVAnalysisResult).where(
            CVAnalysisResult.cv_analysis_request_id == analysis_id
        )
        results = await db.scalar(stmt)

    # Build response
    if results is None:
        return CVAnalysisResultSchema(
            analysis_id=analysis_id,
            status=analysis_req.status,
        )

    # Deserialize JSONB lists into schema objects
    def _as_gap(item):
        # The engine writes gap items as dicts OR as bare strings depending on
        # the LLM output — coerce both into a CVAnalysisGapItem.
        if isinstance(item, dict):
            return CVAnalysisGapItem(**item)
        if isinstance(item, str):
            return CVAnalysisGapItem(capability=item)
        return item

    missing_caps = [_as_gap(i) for i in (results.missing_capabilities or [])]
    weakness_caps = [_as_gap(i) for i in (results.weakness_areas or [])]

    # Deserialize top_matching_positions from job_fit_scores and position IDs
    top_matching = []
    if results.top_matching_position_ids and results.job_fit_scores:
        positions_stmt = select(Position).where(
            Position.id.in_(uuid.UUID(pid) for pid in results.top_matching_position_ids)
        )
        positions_map = {
            str(p.id): p for p in (await db.scalars(positions_stmt)).all()
        }
        for position_id in results.top_matching_position_ids[:10]:
            score = results.job_fit_scores.get(position_id, 0)
            position = positions_map.get(position_id)
            if position:
                top_matching.append(
                    JobFitMatch(
                        position_id=uuid.UUID(position_id),
                        job_title=position.title,
                        company=str(position.company_id) if position.company_id else None,
                        match_score=int(score) if score else 0,
                        semantic_score=int(score) if score else 0,
                        why_fit=f"Matched to {position.title}",
                    )
                )

    # Deserialize improvement suggestions (dicts or bare strings).
    def _as_rec(item):
        if isinstance(item, dict):
            return CVAnalysisRecommendation(**item)
        if isinstance(item, str):
            return CVAnalysisRecommendation(suggestion=item)
        return item

    improvement_sugg = [_as_rec(i) for i in (results.improvement_suggestions or [])]

    return CVAnalysisResultSchema(
        analysis_id=analysis_id,
        status=analysis_req.status,
        missing_capabilities=missing_caps,
        weakness_areas=weakness_caps,
        strength_summary=results.strength_summary,
        top_matching_positions=top_matching,
        total_matching_jobs=len(results.top_matching_position_ids or []),
        improvement_suggestions=improvement_sugg,
        reworded_cv_sections=results.reworded_cv_sections,
        trajectory_analysis=results.trajectory_analysis,
        market_positioning=results.market_positioning,
        growth_opportunities=results.growth_opportunities or [],
    )


@router.get(
    "",
    response_model=PaginatedCVAnalysisList,
    summary="List CV analyses",
    description="List all CV analyses for the current user.",
)
async def list_cv_analyses(
    user: CurrentUser,
    db: DBSession,
    page: int = 1,
    page_size: int = 10,
) -> PaginatedCVAnalysisList:
    """List CV analyses for the current candidate.

    Results are paginated and sorted by most recent first.
    """
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")

    # Get total count using proper SQLAlchemy syntax
    total = await db.scalar(
        select(func.count(CVAnalysisRequest.id)).where(CVAnalysisRequest.user_id == user.id)
    )

    # Get paginated results
    offset = (page - 1) * page_size
    stmt = (
        select(CVAnalysisRequest)
        .where(CVAnalysisRequest.user_id == user.id)
        .order_by(CVAnalysisRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    analyses = (await db.scalars(stmt)).all()

    # Build items
    items = []
    for analysis in analyses:
        # Count gaps
        result = await db.scalar(
            select(CVAnalysisResult).where(
                CVAnalysisResult.cv_analysis_request_id == analysis.id
            )
        )
        gaps_count = 0
        jobs_count = 0
        if result:
            gaps_count = len(result.missing_capabilities or [])
            jobs_count = len(result.top_matching_position_ids or [])

        items.append(
            CVAnalysisListItem(
                analysis_id=analysis.id,
                target_role=analysis.target_role,
                target_seniority=analysis.target_seniority,
                status=analysis.status,
                created_at=analysis.created_at.isoformat(),
                skill_gaps_count=gaps_count,
                matching_jobs_count=jobs_count,
            )
        )

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedCVAnalysisList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{analysis_id}/job-matches",
    summary="Get detailed job matches",
    description="Get detailed job matching results for a CV analysis.",
)
async def get_job_matches(
    analysis_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
):
    """Get detailed job matching for a CV analysis.

    Returns ranked list of best-fitting positions with explanations.
    """
    # Verify ownership
    analysis_req = await db.get(CVAnalysisRequest, analysis_id)
    if analysis_req is None or analysis_req.user_id != user.id:
        raise NotFoundError(
            f"Analysis {analysis_id} not found",
            instance=f"/api/v1/candidates/cv-analysis/{analysis_id}/job-matches",
        )

    if analysis_req.status != CVAnalysisStatus.completed:
        return {
            "status": analysis_req.status,
            "message": "Analysis is still processing",
            "matches": [],
        }

    # Get results
    results = await db.scalar(
        select(CVAnalysisResult).where(
            CVAnalysisResult.cv_analysis_request_id == analysis_id
        )
    )

    if results is None or not results.job_fit_scores:
        return {
            "status": "completed",
            "matches": [],
        }

    # Deserialize job_fit_scores into JobFitMatch objects
    matches = []
    if results.top_matching_position_ids:
        positions_stmt = select(Position).where(
            Position.id.in_(uuid.UUID(pid) for pid in results.top_matching_position_ids)
        )
        positions_map = {
            str(p.id): p for p in (await db.scalars(positions_stmt)).all()
        }
        for position_id in results.top_matching_position_ids[:10]:
            score = results.job_fit_scores.get(position_id, 0)
            position = positions_map.get(position_id)
            if position:
                matches.append(
                    JobFitMatch(
                        position_id=uuid.UUID(position_id),
                        job_title=position.title,
                        company=str(position.company_id) if position.company_id else None,
                        match_score=int(score) if score else 0,
                        semantic_score=int(score) if score else 0,
                        why_fit=f"Aligned to {position.title}",
                    )
                )

    return {
        "status": "completed",
        "matches": matches,
    }
