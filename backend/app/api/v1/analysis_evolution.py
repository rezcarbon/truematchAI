"""Analysis, Matching, and Evolution API - Phase 3-5 REST endpoints.

Endpoints for recruiter workflow:
Phase 3: Analyze assessment responses
Phase 4: Review candidate matches
Phase 5: Track hiring outcomes and learn
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.schemas.analysis_result import AnalysisResultResponse, AnalysisInitiateRequest
from app.schemas.candidate_match import CandidateMatchResponse, MatchInitiateRequest
from app.schemas.hiring_outcome import HiringOutcomeResponse, HiringOutcomeRecordRequest
from app.services.analysis_service import AnalysisService
from app.services.matching_service import MatchingService
from app.services.evolution_service import EvolutionService

logger = logging.getLogger("truematch.analysis_evolution_api")

router = APIRouter()


def require_recruiter(user: User = Depends(get_current_user)) -> User:
    """Dependency: Require recruiter role."""
    if user.role not in (UserRole.recruiter, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can access analysis endpoints",
        )
    return user


# ============================================================================
# PHASE 3: ANALYSIS ENDPOINTS
# ============================================================================


@router.post(
    "/api/v1/assessments/analysis",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Assessment Analysis",
)
async def initiate_analysis(
    request: AnalysisInitiateRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Initiate analysis for completed assessment.

    Agent will analyze responses and score objectively.

    Args:
        request: Assessment ID to analyze
        recruiter: Current recruiter user
        db: Database session

    Returns:
        202 Accepted with analysis_result_id
    """
    try:
        logger.info(
            f"Recruiter {recruiter.id} initiating analysis for "
            f"assessment {request.assessment_id}"
        )

        service = AnalysisService(db)
        analysis = await service.initiate_analysis(request.assessment_id)

        return {
            "analysis_id": str(analysis.id),
            "status": analysis.status.value,
            "assessment_id": str(analysis.assessment_id),
            "created_at": analysis.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error initiating analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initiating analysis",
        )


@router.get(
    "/api/v1/analyses/pending",
    summary="Get Pending Analyses",
)
async def get_pending_analyses(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get pending analysis results for recruiter review."""
    try:
        service = AnalysisService(db)
        analyses, pagination = await service.get_pending_analysis(page, limit)

        return {
            "analyses": [
                {
                    "analysis_id": str(a.id),
                    "candidate_id": str(a.candidate_id),
                    "position_id": str(a.position_id),
                    "overall_confidence": a.overall_confidence,
                    "fairness_score": a.analysis_fairness_check.get("fairness_score", 0),
                    "created_at": a.created_at.isoformat(),
                }
                for a in analyses
            ],
            "pagination": pagination,
        }

    except Exception as e:
        logger.error(f"Error getting pending analyses: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting analyses",
        )


@router.get(
    "/api/v1/analyses/{analysis_id}",
    summary="Get Analysis Details",
)
async def get_analysis_details(
    analysis_id: UUID,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get full analysis details for recruiter review."""
    try:
        service = AnalysisService(db)
        analysis = await service.get_analysis_result(analysis_id)

        return {
            "analysis_id": str(analysis.id),
            "candidate_id": str(analysis.candidate_id),
            "position_id": str(analysis.position_id),
            "status": analysis.status.value,
            "responses_analyzed": analysis.responses_analyzed,
            "scoring_results": analysis.scoring_results,
            "pattern_analysis": analysis.pattern_analysis,
            "overall_metrics": analysis.overall_metrics,
            "recommendation": analysis.recommendation,
            "overall_confidence": analysis.overall_confidence,
            "recruiter_notes": analysis.recruiter_notes,
            "created_at": analysis.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting analysis",
        )


@router.patch(
    "/api/v1/analyses/{analysis_id}/approve",
    summary="Approve Analysis",
)
async def approve_analysis(
    analysis_id: UUID,
    notes: Optional[str] = Query(None),
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recruiter approves analysis result."""
    try:
        service = AnalysisService(db)
        analysis = await service.approve_analysis(analysis_id, recruiter.id, notes)

        logger.info(f"Recruiter {recruiter.id} approved analysis {analysis_id}")

        return {
            "status": "approved",
            "analysis_id": str(analysis_id),
            "analysis_complete_at": analysis.analysis_completed_at.isoformat()
            if analysis.analysis_completed_at
            else None,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error approving analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error approving analysis",
        )


# ============================================================================
# PHASE 4: MATCHING ENDPOINTS
# ============================================================================


@router.post(
    "/api/v1/matches",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Candidate Matching",
)
async def initiate_match(
    request: MatchInitiateRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Initiate matching for analyzed candidate."""
    try:
        logger.info(
            f"Recruiter {recruiter.id} initiating match for "
            f"analysis {request.analysis_result_id}"
        )

        service = MatchingService(db)
        match = await service.initiate_match(request.analysis_result_id)

        return {
            "match_id": str(match.id),
            "status": match.status.value,
            "analysis_result_id": str(match.analysis_result_id),
            "created_at": match.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error initiating match: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initiating match",
        )


@router.get(
    "/api/v1/matches/pending",
    summary="Get Pending Matches",
)
async def get_pending_matches(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    position_id: Optional[UUID] = Query(None),
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get pending matches for recruiter review."""
    try:
        service = MatchingService(db)
        matches, pagination = await service.get_pending_matches(page, limit, position_id)

        return {
            "matches": [
                {
                    "match_id": str(m.id),
                    "candidate_id": str(m.candidate_id),
                    "position_id": str(m.position_id),
                    "overall_score": m.overall_score,
                    "fit_level": m.fit_level.value,
                    "match_confidence": m.match_confidence,
                    "created_at": m.created_at.isoformat(),
                }
                for m in matches
            ],
            "pagination": pagination,
        }

    except Exception as e:
        logger.error(f"Error getting pending matches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting matches",
        )


@router.get(
    "/api/v1/matches/{match_id}",
    summary="Get Match Details",
)
async def get_match_details(
    match_id: UUID,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get full match details."""
    try:
        service = MatchingService(db)
        match = await service.get_match_details(match_id)

        return {
            "match_id": str(match.id),
            "candidate_id": str(match.candidate_id),
            "position_id": str(match.position_id),
            "overall_score": match.overall_score,
            "fit_level": match.fit_level.value,
            "skill_match": match.skill_match,
            "experience_match": match.experience_match,
            "team_fit": match.team_fit,
            "concerns": match.concerns,
            "opportunities": match.opportunities,
            "match_confidence": match.match_confidence,
            "created_at": match.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting match: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting match",
        )


# ============================================================================
# PHASE 5: EVOLUTION ENDPOINTS
# ============================================================================


@router.post(
    "/api/v1/outcomes",
    status_code=status.HTTP_201_CREATED,
    summary="Record Hiring Decision",
)
async def record_outcome(
    request: HiringOutcomeRecordRequest,
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record hiring outcome for learning."""
    try:
        service = EvolutionService(db)
        outcome = await service.record_hiring_decision(
            request.candidate_match_id,
            request.hiring_decision,
            request.decision_rationale,
            request.hire_date,
        )

        logger.info(f"Recruiter {recruiter.id} recorded outcome: {request.hiring_decision}")

        return {
            "outcome_id": str(outcome.id),
            "hiring_decision": outcome.hiring_decision.value,
            "created_at": outcome.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error recording outcome: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording outcome",
        )


@router.get(
    "/api/v1/accuracy",
    summary="Get Prediction Accuracy",
)
async def get_accuracy_metrics(
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get agent prediction accuracy metrics."""
    try:
        service = EvolutionService(db)
        metrics = await service.get_prediction_accuracy()

        logger.info(f"Recruiter {recruiter.id} viewed accuracy metrics")

        return metrics

    except Exception as e:
        logger.error(f"Error getting accuracy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting accuracy metrics",
        )


@router.get(
    "/api/v1/bias-report",
    summary="Get Bias Analysis",
)
async def get_bias_report(
    recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get bias analysis across hiring outcomes."""
    try:
        service = EvolutionService(db)
        report = await service.get_bias_report()

        logger.info(f"Recruiter {recruiter.id} viewed bias report")

        return report

    except Exception as e:
        logger.error(f"Error getting bias report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting bias report",
        )


__all__ = ["router"]
