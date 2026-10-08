"""Retention Prediction API - Post-hire outcome tracking and churn prevention.

Endpoints for predicting attrition risk, tracking retention, and generating coaching recommendations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/api/v1/retention-prediction", tags=["retention"])


class RetentionAssessmentRequest(BaseModel):
    """Request retention risk assessment."""

    hire_id: str = Field(..., description="Hire/employment ID")
    candidate_id: UUID = Field(..., description="Candidate UUID")
    hire_date: str = Field(..., description="Hire date (ISO format)")
    position_id: UUID = Field(..., description="Position UUID")

    # Assessment data
    performance_rating: float = Field(default=3, ge=1, le=5)
    previous_performance_rating: Optional[float] = None
    engagement_score: int = Field(default=100, ge=0, le=100)
    role_satisfaction_score: int = Field(default=100, ge=0, le=100)
    compensation_satisfaction: int = Field(default=100, ge=0, le=100)
    team_dynamics_score: int = Field(default=100, ge=0, le=100)

    # Additional context
    team_size: Optional[int] = None
    manager_tenure_months: Optional[int] = None
    is_first_month: bool = False


class AttritionRiskResponse(BaseModel):
    """Attrition risk assessment."""

    hire_id: str
    candidate_id: str
    risk_score: float
    risk_level: str
    detected_signals: list[str]
    primary_risk_factor: Optional[str]
    days_to_potential_attrition: Optional[int]
    confidence: float


class InterventionResponse(BaseModel):
    """Manager coaching intervention."""

    intervention_type: str
    priority: str
    description: str
    action_steps: list[str]
    expected_impact: str
    success_indicators: list[str]


class RetentionPredictionResponse(BaseModel):
    """Complete retention prediction."""

    hire_id: str
    candidate_id: str
    attrition_risk: AttritionRiskResponse
    recommended_interventions: list[InterventionResponse]
    strengths: list[str]
    challenges: list[str]
    assessment_period: str


@router.post("/assess", response_model=RetentionPredictionResponse)
async def assess_retention_risk(
    request: RetentionAssessmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Assess retention risk for new hire.

    Returns:
    - Attrition risk score (0-1) and risk level
    - Detected early warning signals
    - Estimated days until potential departure
    - Recommended manager coaching interventions
    - Success factors and challenges
    """
    try:
        from app.ml.retention_prediction import RetentionPredictionService
        from datetime import datetime

        service = RetentionPredictionService(db)

        # Parse hire date
        hire_date = datetime.fromisoformat(request.hire_date)

        # Prepare assessment data
        assessment_data = {
            "performance_rating": request.performance_rating,
            "previous_performance_rating": request.previous_performance_rating,
            "engagement_score": request.engagement_score,
            "role_satisfaction_score": request.role_satisfaction_score,
            "compensation_satisfaction": request.compensation_satisfaction,
            "team_dynamics_score": request.team_dynamics_score,
        }

        # Get retention prediction
        prediction = await service.predict_retention(
            hire_id=request.hire_id,
            candidate_id=request.candidate_id,
            position_id=request.position_id,
            hire_date=hire_date,
            assessment_data=assessment_data,
        )

        if not prediction:
            raise HTTPException(status_code=500, detail="Failed to assess retention risk")

        return prediction.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retention assessment error: {str(e)}")


class BulkRetentionAssessmentRequest(BaseModel):
    """Request retention assessments for multiple hires."""

    assessments: list[RetentionAssessmentRequest]


class BulkRetentionAssessmentResponse(BaseModel):
    """Multiple retention predictions."""

    predictions: list[RetentionPredictionResponse]
    high_risk_count: int
    critical_count: int
    average_risk_score: float


@router.post("/assess/bulk", response_model=BulkRetentionAssessmentResponse)
async def assess_bulk_retention(
    request: BulkRetentionAssessmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Assess retention risk for multiple new hires.

    Useful for:
    - Onboarding cohorts
    - Department-wide assessments
    - Risk monitoring dashboards
    """
    try:
        from app.ml.retention_prediction import RetentionPredictionService
        from datetime import datetime

        service = RetentionPredictionService(db)

        predictions = []
        high_risk_count = 0
        critical_count = 0

        for req in request.assessments:
            hire_date = datetime.fromisoformat(req.hire_date)
            assessment_data = {
                "performance_rating": req.performance_rating,
                "previous_performance_rating": req.previous_performance_rating,
                "engagement_score": req.engagement_score,
                "role_satisfaction_score": req.role_satisfaction_score,
                "compensation_satisfaction": req.compensation_satisfaction,
                "team_dynamics_score": req.team_dynamics_score,
            }

            prediction = await service.predict_retention(
                hire_id=req.hire_id,
                candidate_id=req.candidate_id,
                position_id=req.position_id,
                hire_date=hire_date,
                assessment_data=assessment_data,
            )

            if prediction:
                predictions.append(prediction.to_dict())

                # Count risk levels
                if prediction.attrition_risk.risk_level.value == "critical":
                    critical_count += 1
                elif prediction.attrition_risk.risk_level.value == "high":
                    high_risk_count += 1

        avg_risk = sum(p["attrition_risk"]["risk_score"] for p in predictions) / len(
            predictions
        ) if predictions else 0

        return BulkRetentionAssessmentResponse(
            predictions=predictions,
            high_risk_count=high_risk_count,
            critical_count=critical_count,
            average_risk_score=round(avg_risk, 2),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk assessment error: {str(e)}")


@router.get("/trends/{position_id}")
async def get_retention_trends(
    position_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get retention trends for a position.

    Returns:
    - Historical attrition rates
    - Risk patterns by hiring cohort
    - Most common warning signals
    - Intervention effectiveness
    """
    try:
        # Would query historical data
        return {
            "position_id": str(position_id),
            "average_tenure_months": 24,
            "attrition_rate": 0.15,
            "most_common_signals": ["engagement_drop", "role_mismatch"],
            "intervention_effectiveness": {
                "performance_coaching": 0.65,
                "role_discussion": 0.70,
                "compensation_review": 0.55,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis error: {str(e)}")


__all__ = ["router"]
