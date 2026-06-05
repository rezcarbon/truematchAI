"""ATS core features API endpoints: pipeline, interviews, scorecards, analytics."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Sequence

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DBSession
from app.models.application import Application, PipelineStage
from app.models.interview import Interview, InterviewSlot, Scorecard
from app.models.position import Position
from app.models.resume import Resume
from app.schemas.ats import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    InterviewCreate,
    InterviewUpdate,
    InterviewResponse,
    InterviewListResponse,
    ScorecardCreate,
    ScorecardResponse,
    PipelineAnalyticsResponse,
    PipelineStageMetrics,
    SourceAnalyticsResponse,
    SourceMetrics,
)

router = APIRouter()
logger = logging.getLogger("truematch.ats")


# ============================================================================
# APPLICATION / PIPELINE ENDPOINTS
# ============================================================================

@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate, user: CurrentUser, db: DBSession
) -> Application:
    """Create a new application (add candidate to job pipeline)."""
    # Verify position exists
    position = await db.scalar(select(Position).where(Position.id == payload.position_id))
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Verify resume exists
    resume = await db.scalar(select(Resume).where(Resume.id == payload.resume_id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Create application
    application = Application(
        resume_id=payload.resume_id,
        position_id=payload.position_id,
        user_id=user.id,
        source=payload.source,
        tags=payload.tags,
    )
    db.add(application)
    await db.flush()

    logger.info(
        f"Application created for resume {payload.resume_id} to position {payload.position_id}",
        extra={"application_id": str(application.id), "user_id": str(user.id)},
    )
    return application


@router.get("/positions/{position_id}/pipeline", response_model=list[ApplicationResponse])
async def get_pipeline(
    position_id: str,
    stage: str | None = Query(None, description="Filter by stage"),
    user: CurrentUser = None,
    db: DBSession = None,
) -> Sequence[Application]:
    """Get candidates in pipeline for a position."""
    query = select(Application).where(Application.position_id == position_id)

    if stage:
        query = query.where(Application.stage == stage)

    query = query.options(selectinload(Application.interviews))
    applications = await db.scalars(query)
    return applications


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    user: CurrentUser,
    db: DBSession,
) -> Application:
    """Update application (advance stage, add tags, etc)."""
    application = await db.scalar(
        select(Application).where(Application.id == application_id)
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update stage
    old_stage = application.stage
    if payload.stage:
        try:
            new_stage = PipelineStage(payload.stage)
            application.stage = new_stage
            application.stage_entered_at = datetime.utcnow()
            logger.info(
                f"Application stage updated to {payload.stage}",
                extra={"application_id": str(application.id)},
            )

            # Create notification for stage advancement
            from app.services.notification_service import NotificationService
            try:
                await NotificationService.create_notification(
                    db=db,
                    user_id=user.id,
                    notification_type="candidate_advanced",
                    title=f"Candidate advanced to {new_stage.value}",
                    message=f"Application moved from {old_stage.value} to {new_stage.value}",
                    action_url=f"/applications/{application_id}",
                    broadcast_websocket=True,
                )
            except Exception as e:
                logger.error(f"Failed to create notification: {str(e)}")
                # Don't fail the update if notification creation fails

        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {payload.stage}")

    # Update tags
    if payload.tags is not None:
        application.tags = payload.tags

    # Update source
    if payload.source is not None:
        application.source = payload.source

    await db.flush()
    return application


# ============================================================================
# INTERVIEW ENDPOINTS
# ============================================================================

@router.post("/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def schedule_interview(
    payload: InterviewCreate, user: CurrentUser, db: DBSession
) -> Interview:
    """Schedule an interview."""
    # Verify application exists
    application = await db.scalar(
        select(Application).where(Application.id == payload.application_id)
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Create interview
    interview = Interview(
        application_id=payload.application_id,
        position_id=payload.position_id,
        interviewer_ids=payload.interviewer_ids,
        meeting_platform=payload.meeting_platform,
        meeting_link=payload.meeting_link,
    )
    db.add(interview)
    await db.flush()

    logger.info(
        f"Interview scheduled for application {payload.application_id}",
        extra={"interview_id": str(interview.id)},
    )

    # Create notifications for interviewers
    from app.services.notification_service import NotificationService
    try:
        for interviewer_id in payload.interviewer_ids or []:
            await NotificationService.create_notification(
                db=db,
                user_id=interviewer_id,
                notification_type="interview_scheduled",
                title=f"Interview scheduled - {payload.meeting_platform}",
                message=f"You have an interview scheduled. Meeting link: {payload.meeting_link}",
                action_url=f"/interviews/{interview.id}",
                broadcast_websocket=True,
            )
    except Exception as e:
        logger.error(f"Failed to create interview notifications: {str(e)}")
        # Don't fail the interview creation if notifications fail

    return interview


@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
async def get_interview(interview_id: str, user: CurrentUser, db: DBSession) -> Interview:
    """Get interview details."""
    interview = await db.scalar(
        select(Interview)
        .where(Interview.id == interview_id)
        .options(selectinload(Interview.scorecards))
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.get("/applications/{application_id}/interviews", response_model=InterviewListResponse)
async def list_interviews(
    application_id: str, user: CurrentUser, db: DBSession, page: int = 1, page_size: int = 10
) -> InterviewListResponse:
    """List interviews for an application."""
    query = select(Interview).where(Interview.application_id == application_id)

    # Count total
    total = await db.scalar(select(func.count()).select_from(Interview).where(Interview.application_id == application_id))

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    interviews = await db.scalars(query)

    return InterviewListResponse(
        items=list(interviews),
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.patch("/interviews/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: str,
    payload: InterviewUpdate,
    user: CurrentUser,
    db: DBSession,
) -> Interview:
    """Update interview details."""
    interview = await db.scalar(select(Interview).where(Interview.id == interview_id))
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if payload.scheduled_at:
        interview.scheduled_at = payload.scheduled_at
    if payload.interviewer_ids:
        interview.interviewer_ids = payload.interviewer_ids
    if payload.meeting_platform:
        interview.meeting_platform = payload.meeting_platform
    if payload.meeting_link:
        interview.meeting_link = payload.meeting_link
    if payload.status:
        interview.status = payload.status

    await db.flush()
    return interview


# ============================================================================
# SCORECARD ENDPOINTS
# ============================================================================

@router.post("/scorecards", response_model=ScorecardResponse, status_code=status.HTTP_201_CREATED)
async def submit_scorecard(
    payload: ScorecardCreate, user: CurrentUser, db: DBSession
) -> Scorecard:
    """Submit interview scorecard."""
    # Verify interview exists
    interview = await db.scalar(select(Interview).where(Interview.id == payload.interview_id))
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Create scorecard
    scorecard = Scorecard(
        interview_id=payload.interview_id,
        interviewer_id=user.id,
        position_id=interview.position_id,
        competency_scores=payload.competency_scores,
        feedback=payload.feedback,
        overall_recommendation=payload.overall_recommendation,
        submitted_at=datetime.utcnow(),
    )
    db.add(scorecard)
    await db.flush()

    logger.info(
        f"Scorecard submitted for interview {payload.interview_id}",
        extra={"scorecard_id": str(scorecard.id), "interviewer_id": str(user.id)},
    )

    # Create notifications for hiring managers
    from app.services.notification_service import NotificationService
    try:
        # Notify the recruiter who requested the scorecard
        await NotificationService.create_notification(
            db=db,
            user_id=interview.position_id,  # Position owner (recruiter)
            notification_type="scorecard_request",
            title="Scorecard submitted",
            message=f"{user.display_name} submitted their interview scorecard",
            action_url=f"/interviews/{interview.id}/scorecards",
            broadcast_websocket=True,
        )
    except Exception as e:
        logger.error(f"Failed to create scorecard notification: {str(e)}")
        # Don't fail the scorecard submission if notification fails

    return scorecard


@router.get("/interviews/{interview_id}/scorecards", response_model=list[ScorecardResponse])
async def get_interview_scorecards(
    interview_id: str, user: CurrentUser, db: DBSession
) -> Sequence[Scorecard]:
    """Get all scorecards for an interview."""
    scorecards = await db.scalars(
        select(Scorecard).where(Scorecard.interview_id == interview_id)
    )
    return scorecards


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/positions/{position_id}/pipeline-analytics", response_model=PipelineAnalyticsResponse)
async def get_pipeline_analytics(
    position_id: str, user: CurrentUser, db: DBSession
) -> PipelineAnalyticsResponse:
    """Get pipeline metrics for a position."""
    # Get all applications for position
    applications = await db.scalars(
        select(Application).where(Application.position_id == position_id)
    )
    apps_list = list(applications)

    # Count by stage
    by_stage = []
    for stage in PipelineStage:
        count = len([a for a in apps_list if a.stage == stage])
        if count > 0:
            # Calculate days in stage
            now = datetime.utcnow()
            stage_apps = [a for a in apps_list if a.stage == stage]
            days_in_stage = [
                (now - a.stage_entered_at).days for a in stage_apps
                if a.stage_entered_at
            ]
            avg_days = sum(days_in_stage) / len(days_in_stage) if days_in_stage else 0
            median_days = sorted(days_in_stage)[len(days_in_stage) // 2] if days_in_stage else 0

            by_stage.append(
                PipelineStageMetrics(
                    stage=stage.value,
                    count=count,
                    average_days_in_stage=avg_days,
                    median_days_in_stage=median_days,
                )
            )

    # Calculate time to hire (applied -> hired)
    hired_apps = [a for a in apps_list if a.stage == PipelineStage.hired]
    times_to_hire = [
        (a.updated_at - a.applied_at).days for a in hired_apps
        if a.applied_at and a.updated_at
    ]
    avg_time_to_hire = sum(times_to_hire) / len(times_to_hire) if times_to_hire else 0

    # Calculate conversion rates between stages
    conversion_rates = {}
    all_stages = [s for s in PipelineStage]
    for i, stage in enumerate(all_stages[:-1]):
        current_stage_apps = [a for a in apps_list if a.stage == stage]
        next_stage = all_stages[i + 1]
        converted_apps = [a for a in apps_list if a.stage == next_stage]

        if current_stage_apps:
            rate = (len(converted_apps) / len(current_stage_apps)) * 100
            conversion_rates[f"{stage.value}_to_{next_stage.value}"] = round(rate, 2)

    return PipelineAnalyticsResponse(
        position_id=position_id,
        total_applications=len(apps_list),
        by_stage=by_stage,
        conversion_rates=conversion_rates,
        average_time_to_hire=avg_time_to_hire,
    )


@router.get("/source-analytics", response_model=SourceAnalyticsResponse)
async def get_source_analytics(
    position_id: str | None = Query(None),
    user: CurrentUser = None,
    db: DBSession = None,
) -> SourceAnalyticsResponse:
    """Get source effectiveness analytics."""
    query = select(Application)
    if position_id:
        query = query.where(Application.position_id == position_id)

    applications = await db.scalars(query)
    apps_list = list(applications)

    # Group by source and calculate metrics
    by_source = {}
    for app in apps_list:
        source = app.source or "unknown"
        if source not in by_source:
            by_source[source] = {
                "applications": 0,
                "hires": 0,
                "times_to_hire": [],
            }
        by_source[source]["applications"] += 1
        if app.stage == PipelineStage.hired:
            by_source[source]["hires"] += 1
            # Calculate time to hire for this application
            if app.applied_at and app.updated_at:
                time_to_hire_days = (app.updated_at - app.applied_at).days
                by_source[source]["times_to_hire"].append(time_to_hire_days)

    # Calculate metrics per source
    source_metrics = []
    for source, data in by_source.items():
        hire_rate = (data["hires"] / data["applications"] * 100) if data["applications"] > 0 else 0
        # Calculate average time to hire for this source
        avg_time_to_hire = (
            sum(data["times_to_hire"]) / len(data["times_to_hire"])
            if data["times_to_hire"]
            else 0
        )
        source_metrics.append(
            SourceMetrics(
                source=source,
                applications=data["applications"],
                hires=data["hires"],
                hire_rate=hire_rate,
                average_time_to_hire=avg_time_to_hire,
            )
        )

    return SourceAnalyticsResponse(
        position_id=position_id,
        by_source=source_metrics,
    )
