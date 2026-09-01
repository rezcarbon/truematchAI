"""JD simulation endpoints for recruiters."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func, and_

from app.core.exceptions import NotFoundError, AuthorizationError, ValidationError
from app.deps import CurrentUser, DBSession, require_role
from app.models.jd_simulation import JDSimulationRequest, JDSimulationResult, JDSimulationStatus
from app.models.position import Position
from app.models.user import UserRole
from app.schemas.jd_simulation import (
    ArchetypeFit,
    CapabilityGapItem,
    CreepWarning,
    DetailedJDAnalysisRequest,
    DetailedJDAnalysisResponse,
    JDSimulationListItem,
    JDSimulationResult as JDSimulationResultSchema,
    JDSimulationStartRequest,
    JDSimulationStartResponse,
    PaginatedJDSimulationList,
    PaginatedSimulationHistory,
    SimulationHistoryItem,
    SuggestionAcceptanceRequest,
    SuggestionAcceptanceResponse,
    WordingSuggestion,
)

router = APIRouter(prefix="/recruiters/jd-simulation", tags=["jd-simulation"])
logger = logging.getLogger("truematch.jd_simulation")


@router.post(
    "",
    response_model=JDSimulationStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start JD simulation",
    description="Initiate a JD simulation request. Returns 202 Accepted with simulation_id for polling.",
)
async def start_jd_simulation(
    payload: JDSimulationStartRequest,
    user: CurrentUser,
    db: DBSession,
) -> JDSimulationStartResponse:
    """Start a JD simulation for analysis.

    Can either analyze an existing position or paste a new JD.
    The simulation will be queued for async processing.
    """
    # Validate that either position_id or jd_text is provided
    if payload.position_id is None and payload.jd_text is None:
        raise ValueError(
            "Either position_id or jd_text must be provided"
        )
    if payload.position_id is not None and payload.jd_text is not None:
        raise ValueError(
            "Provide either position_id or jd_text, not both"
        )

    # If position_id provided, verify it exists and belongs to user's company
    if payload.position_id:
        position = await db.get(Position, payload.position_id)
        if position is None or (position.company_id and position.created_by != user.id):
            raise NotFoundError(
                f"Position {payload.position_id} not found",
                instance="/api/v1/recruiters/jd-simulation",
            )

    # Create simulation request
    simulation_req = JDSimulationRequest(
        id=uuid.uuid4(),
        user_id=user.id,
        position_id=payload.position_id,
        jd_text=payload.jd_text,
        simulation_type=payload.simulation_type,
        target_candidate_profile=payload.target_candidate_profile,
    )
    db.add(simulation_req)
    await db.flush()

    logger.info(
        "JD simulation started",
        extra={
            "simulation_id": str(simulation_req.id),
            "user_id": str(user.id),
            "position_id": str(payload.position_id) if payload.position_id else None,
            "simulation_type": payload.simulation_type.value,
        },
    )

    # Commit the request first so it exists in the DB before the worker reads it
    await db.commit()

    # Enqueue the async task to the worker
    from app.workers.jd_simulation import process_jd_simulation_task
    process_jd_simulation_task.delay(str(simulation_req.id))

    return JDSimulationStartResponse(
        simulation_id=simulation_req.id,
        status=simulation_req.status,
    )


@router.get(
    "/{simulation_id}",
    response_model=JDSimulationResultSchema,
    summary="Get JD simulation results",
    description="Retrieve the results of a JD simulation request.",
)
async def get_jd_simulation(
    simulation_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> JDSimulationResultSchema:
    """Get JD simulation results by ID.

    Returns simulation status and results once processing is complete.
    """
    # Get simulation request
    simulation_req = await db.get(JDSimulationRequest, simulation_id)
    if simulation_req is None or simulation_req.user_id != user.id:
        raise NotFoundError(
            f"Simulation {simulation_id} not found",
            instance=f"/api/v1/recruiters/jd-simulation/{simulation_id}",
        )

    # Get results if completed
    results = None
    if simulation_req.status == JDSimulationStatus.completed:
        stmt = select(JDSimulationResult).where(
            JDSimulationResult.jd_simulation_request_id == simulation_id
        )
        results = await db.scalar(stmt)

    # Build response
    if results is None:
        return JDSimulationResultSchema(
            simulation_id=simulation_id,
            status=simulation_req.status,
        )

    # Deserialize JSONB lists into schema objects
    critical_caps = []
    if results.critical_capabilities:
        critical_caps = [
            CapabilityGapItem(**item) if isinstance(item, dict) else item
            for item in results.critical_capabilities
        ]

    capability_recs = []
    if results.capability_recommendations:
        capability_recs = [
            CapabilityGapItem(**item) if isinstance(item, dict) else item
            for item in results.capability_recommendations
        ]

    creep_warns = []
    if results.creep_warnings:
        creep_warns = [
            CreepWarning(**item) if isinstance(item, dict) else item
            for item in results.creep_warnings
        ]

    # Deserialize fit_by_archetype dict into list of ArchetypeFit objects
    archetype_fits = []
    if results.fit_by_archetype:
        # Handle both dict and list formats
        if isinstance(results.fit_by_archetype, dict):
            for archetype_name, fit_data in results.fit_by_archetype.items():
                if isinstance(fit_data, dict):
                    archetype_fits.append(ArchetypeFit(**fit_data))
                else:
                    # If it's just a score, create a minimal ArchetypeFit
                    archetype_fits.append(
                        ArchetypeFit(
                            archetype=archetype_name,
                            fit_score=int(fit_data) if isinstance(fit_data, (int, float)) else 0,
                        )
                    )
        elif isinstance(results.fit_by_archetype, list):
            archetype_fits = [
                ArchetypeFit(**item) if isinstance(item, dict) else item
                for item in results.fit_by_archetype
            ]

    # Deserialize capability_verbiage_suggestions
    wording_sugg = []
    if results.capability_verbiage_suggestions:
        wording_sugg = [
            WordingSuggestion(**item) if isinstance(item, dict) else item
            for item in results.capability_verbiage_suggestions
        ]

    return JDSimulationResultSchema(
        simulation_id=simulation_id,
        status=simulation_req.status,
        critical_capabilities=critical_caps,
        missing_clarity=results.missing_clarity or [],
        capability_recommendations=capability_recs,
        requirement_difficulty_score=results.requirement_difficulty_score or 0,
        experience_years_assessment=results.experience_years_assessment,
        tech_stack_balance=results.tech_stack_balance,
        creep_warnings=creep_warns,
        fit_by_archetype=archetype_fits,
        best_archetype_fit=results.best_archetype_fit,
        talent_pool_estimate=results.talent_pool_estimate,
        quality_score=results.quality_score or 0,
        market_positioning=results.market_positioning,
        missing_sections=results.missing_sections or [],
        quality_issues=results.quality_issues or [],
        suggested_job_title_variations=results.suggested_job_title_variations or [],
        improved_role_description=results.improved_role_description,
        capability_verbiage_suggestions=wording_sugg,
        benefits_suggestions=results.benefits_suggestions or [],
        culture_fit_language=results.culture_fit_language,
    )


@router.get(
    "",
    response_model=PaginatedJDSimulationList,
    summary="List JD simulations",
    description="List all JD simulations for the current user.",
)
async def list_jd_simulations(
    user: CurrentUser,
    db: DBSession,
    page: int = 1,
    page_size: int = 10,
) -> PaginatedJDSimulationList:
    """List JD simulations for the current recruiter.

    Results are paginated and sorted by most recent first.
    """
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")

    # Get total count using proper SQLAlchemy syntax
    total = await db.scalar(
        select(func.count(JDSimulationRequest.id)).where(JDSimulationRequest.user_id == user.id)
    )

    # Get paginated results
    offset = (page - 1) * page_size
    stmt = (
        select(JDSimulationRequest)
        .where(JDSimulationRequest.user_id == user.id)
        .order_by(JDSimulationRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    simulations = (await db.scalars(stmt)).all()

    # Build items
    items = []
    for simulation in simulations:
        # Count findings
        result = await db.scalar(
            select(JDSimulationResult).where(
                JDSimulationResult.jd_simulation_request_id == simulation.id
            )
        )
        gaps_count = 0
        creep_count = 0
        quality_score = None
        if result:
            gaps_count = len(result.critical_capabilities or [])
            creep_count = len(result.creep_warnings or [])
            quality_score = result.quality_score

        items.append(
            JDSimulationListItem(
                simulation_id=simulation.id,
                position_id=simulation.position_id,
                simulation_type=simulation.simulation_type,
                status=simulation.status,
                created_at=simulation.created_at.isoformat(),
                quality_score=quality_score,
                capability_gaps_count=gaps_count,
                creep_warnings_count=creep_count,
            )
        )

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedJDSimulationList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{simulation_id}/candidate-fit",
    summary="Get candidate archetype fit",
    description="Get detailed candidate archetype fit analysis for a JD simulation.",
)
async def get_candidate_fit(
    simulation_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
):
    """Get detailed candidate archetype fit for a JD simulation.

    Returns fit scores for junior, mid, senior, and lead archetypes.
    """
    # Verify ownership
    simulation_req = await db.get(JDSimulationRequest, simulation_id)
    if simulation_req is None or simulation_req.user_id != user.id:
        raise NotFoundError(
            f"Simulation {simulation_id} not found",
            instance=f"/api/v1/recruiters/jd-simulation/{simulation_id}/candidate-fit",
        )

    if simulation_req.status != JDSimulationStatus.completed:
        return {
            "status": simulation_req.status,
            "message": "Simulation is still processing",
            "archetypes": [],
        }

    # Get results
    results = await db.scalar(
        select(JDSimulationResult).where(
            JDSimulationResult.jd_simulation_request_id == simulation_id
        )
    )

    if results is None or not results.fit_by_archetype:
        return {
            "status": "completed",
            "archetypes": [],
        }

    # Deserialize fit_by_archetype dict/list into ArchetypeFit objects
    archetype_list = []
    if isinstance(results.fit_by_archetype, dict):
        # Handle dict format: {archetype_name: score_or_data}
        for archetype_name, fit_data in results.fit_by_archetype.items():
            if isinstance(fit_data, dict):
                # Full ArchetypeFit data
                archetype_list.append(ArchetypeFit(**fit_data))
            else:
                # Just a score - create minimal ArchetypeFit
                archetype_list.append(
                    ArchetypeFit(
                        archetype=archetype_name,
                        fit_score=int(fit_data) if isinstance(fit_data, (int, float)) else 0,
                    )
                )
    elif isinstance(results.fit_by_archetype, list):
        # Handle list format: [ArchetypeFit objects]
        for item in results.fit_by_archetype:
            if isinstance(item, dict):
                archetype_list.append(ArchetypeFit(**item))
            else:
                archetype_list.append(item)

    return {
        "status": "completed",
        "archetypes": archetype_list,
    }


@router.get(
    "/{simulation_id}/suggested-postings",
    summary="Get wording suggestions",
    description="Get suggested JD wording and phrasing improvements.",
)
async def get_suggested_postings(
    simulation_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
):
    """Get wording suggestions for a JD simulation.

    Returns improved titles, descriptions, and capability phrasings.
    """
    # Verify ownership
    simulation_req = await db.get(JDSimulationRequest, simulation_id)
    if simulation_req is None or simulation_req.user_id != user.id:
        raise NotFoundError(
            f"Simulation {simulation_id} not found",
            instance=f"/api/v1/recruiters/jd-simulation/{simulation_id}/suggested-postings",
        )

    if simulation_req.status != JDSimulationStatus.completed:
        return {
            "status": simulation_req.status,
            "message": "Simulation is still processing",
            "suggestions": None,
        }

    # Get results
    results = await db.scalar(
        select(JDSimulationResult).where(
            JDSimulationResult.jd_simulation_request_id == simulation_id
        )
    )

    if results is None:
        return {
            "status": "completed",
            "suggestions": None,
        }

    return {
        "status": "completed",
        "suggestions": {
            "job_title_variations": results.suggested_job_title_variations,
            "role_description": results.improved_role_description,
            "capability_phrasings": results.capability_verbiage_suggestions,
            "benefits": results.benefits_suggestions,
            "culture_fit": results.culture_fit_language,
        },
    }


@router.post(
    "/detailed",
    response_model=DetailedJDAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze JD with detailed scoring",
    description="Perform detailed analysis of a job description with multi-dimensional scoring.",
)
async def analyze_jd_detailed(
    payload: DetailedJDAnalysisRequest,
    user: Annotated[CurrentUser, Depends(require_role(UserRole.recruiter, UserRole.admin))],
    db: DBSession,
) -> DetailedJDAnalysisResponse:
    """Analyze a job description in detail.

    Provides comprehensive scoring across multiple dimensions including:
    - Clarity and specificity
    - Requirement realism
    - Candidate pool estimates
    - Market positioning

    This endpoint requires recruiter or admin role and has rate limiting applied.
    """
    if not payload.jd_text or len(payload.jd_text.strip()) < 10:
        raise ValidationError(
            message="JD text must be at least 10 characters",
            instance="/api/v1/recruiters/jd-simulation/detailed",
        )

    logger.info(
        "Detailed JD analysis initiated",
        extra={
            "user_id": str(user.id),
            "position_title": payload.position_title,
            "jd_length": len(payload.jd_text),
        },
    )

    # TODO: Integrate with JD simulation engine for actual analysis
    # This is a placeholder response showing the expected structure
    return DetailedJDAnalysisResponse(
        score=75,
        dimensions={
            "clarity": 80,
            "specificity": 75,
            "requirement_realism": 70,
            "market_competitiveness": 75,
            "candidate_pool_fit": 75,
        },
        issues=[
            "Requirement creep detected in tech stack specification",
            "Years of experience unclear for junior candidates",
        ],
        suggestions=[
            {
                "suggestion_id": "sugg-001",
                "priority": "high",
                "category": "requirement_clarity",
                "text": "Clarify required vs. preferred tech stack skills",
                "expected_impact": "Increases candidate pool by 25%",
            },
            {
                "suggestion_id": "sugg-002",
                "priority": "medium",
                "category": "phrasing",
                "text": "Replace 'must have' with 'we prefer' for secondary skills",
                "expected_impact": "Improves candidate experience",
            },
        ],
    )


@router.post(
    "/accept-suggestion",
    response_model=SuggestionAcceptanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept and apply JD suggestion",
    description="Accept a suggestion and update the JD text.",
)
async def accept_jd_suggestion(
    payload: SuggestionAcceptanceRequest,
    user: Annotated[CurrentUser, Depends(require_role(UserRole.recruiter, UserRole.admin))],
    db: DBSession,
) -> SuggestionAcceptanceResponse:
    """Accept a JD improvement suggestion and apply the modification.

    Updates the JD with the suggested change and records the acceptance
    for audit and learning purposes.
    """
    if not payload.modified_text or len(payload.modified_text.strip()) < 10:
        raise ValidationError(
            message="Modified text must be at least 10 characters",
            instance="/api/v1/recruiters/jd-simulation/accept-suggestion",
        )

    logger.info(
        "JD suggestion accepted",
        extra={
            "user_id": str(user.id),
            "suggestion_id": payload.suggestion_id,
        },
    )

    # TODO: Store the accepted suggestion in audit log or tracking table
    now = datetime.now(timezone.utc).isoformat()

    return SuggestionAcceptanceResponse(
        updated_jd=payload.modified_text,
        suggestion_id=payload.suggestion_id,
        timestamp=now,
    )


@router.get(
    "/history",
    response_model=PaginatedSimulationHistory,
    status_code=status.HTTP_200_OK,
    summary="Get simulation history",
    description="Retrieve paginated history of JD simulations for the current user.",
)
async def get_simulation_history(
    user: Annotated[CurrentUser, Depends(require_role(UserRole.recruiter, UserRole.admin))],
    db: DBSession,
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> PaginatedSimulationHistory:
    """Retrieve simulation history for the current recruiter.

    Returns a paginated list of all simulations performed by the user,
    with most recent first. Includes basic metadata and preview of JD text.
    """
    if limit < 1 or limit > 100:
        raise ValidationError(
            message="limit must be between 1 and 100",
            instance="/api/v1/recruiters/jd-simulation/history",
        )

    # Get total count
    total = await db.scalar(
        select(func.count(JDSimulationRequest.id)).where(
            JDSimulationRequest.user_id == user.id
        )
    )

    # Get paginated results
    stmt = (
        select(JDSimulationRequest)
        .where(JDSimulationRequest.user_id == user.id)
        .order_by(JDSimulationRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    simulations = (await db.scalars(stmt)).all()

    # Build items
    items = []
    for simulation in simulations:
        # Get position title if available
        position_title = None
        if simulation.position_id:
            position = await db.get(Position, simulation.position_id)
            if position:
                position_title = position.title

        # Get results if completed
        completed_at = None
        quality_score = None
        if simulation.status == JDSimulationStatus.completed:
            results = await db.scalar(
                select(JDSimulationResult).where(
                    JDSimulationResult.jd_simulation_request_id == simulation.id
                )
            )
            if results:
                completed_at = results.updated_at.isoformat() if results.updated_at else None
                quality_score = results.quality_score

        # Create JD text preview
        jd_text = simulation.jd_text or ""
        jd_preview = (jd_text[:200] + "...") if len(jd_text) > 200 else jd_text

        items.append(
            SimulationHistoryItem(
                simulation_id=simulation.id,
                position_id=simulation.position_id,
                position_title=position_title,
                jd_text_preview=jd_preview,
                simulation_type=simulation.simulation_type,
                status=simulation.status,
                quality_score=quality_score,
                created_at=simulation.created_at.isoformat(),
                completed_at=completed_at,
            )
        )

    logger.info(
        "Simulation history retrieved",
        extra={
            "user_id": str(user.id),
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )

    return PaginatedSimulationHistory(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
