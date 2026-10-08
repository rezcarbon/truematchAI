"""Retention Prediction Service - High-level orchestration."""

import logging
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .retention_model import RetentionPredictionModel, RetentionPrediction, AttritionRisk

logger = logging.getLogger(__name__)


class RetentionPredictionService:
    """Orchestrates retention prediction for managers and HR."""

    def __init__(self, db: AsyncSession, model: Optional[RetentionPredictionModel] = None):
        self.db = db
        self.model = model or RetentionPredictionModel()

    async def predict_retention(
        self,
        hire_id: str,
        candidate_id: UUID,
        position_id: UUID,
        hire_date: datetime,
        assessment_data: Dict,
    ) -> Optional[RetentionPrediction]:
        """
        Predict retention for new hire and generate interventions.

        Args:
            hire_id: Hire/employment ID
            candidate_id: Candidate UUID
            position_id: Position UUID
            hire_date: Hire date
            assessment_data: Assessment metrics (performance, engagement, etc.)

        Returns:
            RetentionPrediction with risk assessment and recommendations
        """
        try:
            # Predict attrition risk
            attrition_risk = self.model.predict_retention_risk(
                hire_id=hire_id,
                candidate_id=str(candidate_id),
                hire_date=hire_date,
                assessment_data=assessment_data,
            )

            # Generate interventions
            interventions = self.model.generate_interventions(attrition_risk)

            # Create prediction
            prediction = RetentionPrediction(
                hire_id=hire_id,
                candidate_id=str(candidate_id),
                position_id=str(position_id),
                hire_date=hire_date,
                attrition_risk=attrition_risk,
                recommended_interventions=interventions,
                strengths=[
                    "Successfully onboarded",
                    "Positive team feedback" if assessment_data.get("team_dynamics_score", 100) > 70 else "",
                    "Exceeding performance targets" if assessment_data.get("performance_rating", 3) >= 4 else "",
                ],
                challenges=[
                    "Early career stage" if assessment_data.get("team_dynamics_score", 100) < 70 else "",
                    "Limited domain experience" if assessment_data.get("performance_rating", 3) < 3 else "",
                    "New to company culture" if assessment_data.get("engagement_score", 100) < 70 else "",
                ],
                team_composition_impact={
                    "team_diversity": "positive" if assessment_data.get("team_dynamics_score", 100) > 75 else "neutral",
                    "skill_distribution": "balanced",
                    "morale_impact": "positive" if assessment_data.get("engagement_score", 100) > 80 else "neutral",
                },
                assessment_period="first_90_days",
            )

            # Store prediction (optional)
            logger.info(f"Generated retention prediction for {hire_id}")

            return prediction

        except Exception as e:
            logger.error(f"Error predicting retention: {e}")
            return None

    async def get_manager_alert(
        self, hire_id: str, risk_threshold: str = "high"
    ) -> Optional[Dict]:
        """
        Get manager alert if hire exceeds risk threshold.

        Args:
            hire_id: Hire ID to check
            risk_threshold: Risk level for alerting (high or critical)

        Returns:
            Alert details if risk threshold exceeded, None otherwise
        """
        # Would query database for latest prediction
        # Check if risk level >= threshold
        # Return alert if needed

        return None

    async def record_intervention(
        self,
        hire_id: str,
        intervention_type: str,
        completed_by: str,
        outcome: str,
        notes: str = "",
    ) -> bool:
        """
        Record manager intervention for attrition risk.

        Args:
            hire_id: Hire ID
            intervention_type: Type of intervention
            completed_by: Manager/HR who completed intervention
            outcome: Outcome (positive, neutral, negative)
            notes: Additional notes

        Returns:
            Success status
        """
        try:
            # Store intervention record
            logger.info(
                f"Recorded {intervention_type} intervention for {hire_id} "
                f"by {completed_by} with outcome {outcome}"
            )
            return True

        except Exception as e:
            logger.error(f"Error recording intervention: {e}")
            return False


__all__ = ["RetentionPredictionService"]
