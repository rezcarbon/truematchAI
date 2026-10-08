"""Forecast Service - Orchestrates pipeline forecasting for recruiters."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.models.application_timeline import ApplicationTimeline, EventType
from app.models.hiring_outcome import HiringOutcome, HiringDecision
from app.models.assessment import Assessment
from .forecast_model import ForecastModel, PipelineForecast

logger = logging.getLogger(__name__)


class ForecastService:
    """High-level service for pipeline forecasting."""

    def __init__(self, db: AsyncSession, model: Optional[ForecastModel] = None):
        self.db = db
        self.model = model or ForecastModel()

    async def forecast_position(self, position_id: UUID) -> Optional[PipelineForecast]:
        """
        Forecast time-to-hire for a specific position.

        Args:
            position_id: Position UUID

        Returns:
            PipelineForecast with prediction and recommendations
        """
        try:
            # Get position data
            position = await self._get_position(position_id)
            if not position:
                logger.warning(f"Position {position_id} not found")
                return None

            # Extract features
            features = await self._extract_position_features(position)

            # Make prediction
            if not self.model.is_trained:
                logger.warning("Model not trained, using fallback prediction")
                prediction = self._fallback_prediction(position)
            else:
                pred_dict = self.model.predict(features)
                days_to_fill = pred_dict["days_to_fill"]
                confidence = pred_dict["confidence"]
                prediction = {
                    "days_to_fill": days_to_fill,
                    "confidence": confidence,
                }

            # Identify bottleneck stage
            bottleneck = await self._identify_bottleneck(position_id)

            # Generate recommendations
            recommendations = self._generate_recommendations(bottleneck, position.department)

            # Create forecast
            fill_date = datetime.utcnow() + timedelta(days=prediction["days_to_fill"])

            forecast = PipelineForecast(
                position_id=str(position_id),
                forecasted_fill_date=fill_date,
                estimated_days_to_fill=prediction["days_to_fill"],
                confidence=prediction["confidence"],
                bottleneck_stage=bottleneck,
                recommendations=recommendations,
                created_at=datetime.utcnow(),
            )

            return forecast

        except Exception as e:
            logger.error(f"Error forecasting position {position_id}: {e}")
            return None

    async def _get_position(self, position_id: UUID) -> Optional[Position]:
        """Fetch position from database."""
        stmt = select(Position).where(Position.id == position_id)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def _extract_position_features(self, position: Position) -> list:
        """Extract ML features from a position."""
        # Job title length
        job_title_length = len(position.job_title.split()) if position.job_title else 0

        # Skill count
        skill_count = len(position.required_skills) if position.required_skills else 0

        # Salary range
        salary_range = 0
        if position.salary_min and position.salary_max:
            salary_range = (position.salary_max - position.salary_min) / 1000

        # Salary midpoint (normalized)
        salary_mid = 0
        if position.salary_min and position.salary_max:
            salary_mid = (position.salary_min + position.salary_max) / 2 / 100000

        # Current application count
        stmt = select(func.count(Assessment.id)).where(
            Assessment.position_id == position.id
        )
        result = await self.db.execute(stmt)
        application_count = result.scalar() or 0

        return [
            float(job_title_length),
            float(skill_count),
            float(salary_range),
            float(salary_mid),
            float(application_count),
        ]

    async def _identify_bottleneck(self, position_id: UUID) -> Optional[str]:
        """
        Identify which stage is slowing the hiring pipeline.

        Looks at application timeline events and identifies the longest stage.
        """
        stmt = select(ApplicationTimeline).where(
            ApplicationTimeline.position_id == position_id,  # Assuming this relationship exists
            ApplicationTimeline.is_active == True,
        )
        result = await self.db.execute(stmt)
        timelines = result.scalars().all()

        if not timelines:
            return None

        # Analyze event type distribution
        stage_times = {}
        for timeline in timelines:
            if timeline.events:
                for i, event in enumerate(timeline.events[:-1]):
                    if i + 1 < len(timeline.events):
                        event_type = event.get("type")
                        next_event = timeline.events[i + 1]
                        time_diff = (
                            next_event.get("timestamp") - event.get("timestamp")
                        )
                        if event_type not in stage_times:
                            stage_times[event_type] = []
                        stage_times[event_type].append(time_diff)

        # Find stage with longest average duration
        if not stage_times:
            return None

        avg_times = {
            stage: sum(times) / len(times)
            for stage, times in stage_times.items()
        }
        bottleneck = max(avg_times, key=avg_times.get)

        return bottleneck

    def _generate_recommendations(
        self, bottleneck_stage: Optional[str], department: Optional[str]
    ) -> list[str]:
        """Generate recruiter action recommendations based on bottleneck."""
        recommendations = []

        if bottleneck_stage == EventType.interview_scheduled:
            recommendations.extend([
                "Expedite interview scheduling - this is your bottleneck",
                "Consider parallel interview tracks to speed up process",
                "Align interviews with candidate availability to minimize delays",
            ])
        elif bottleneck_stage == EventType.offer_extended:
            recommendations.extend([
                "Streamline offer preparation process",
                "Pre-prepare offer documents to reduce turnaround",
                "Have offers reviewed and ready before final interview",
            ])
        elif bottleneck_stage == EventType.feedback_shared:
            recommendations.extend([
                "Establish clear feedback deadlines (24-48 hours)",
                "Use async feedback collection if interviewer alignment possible",
                "Reduce interview panel size for faster decisions",
            ])
        else:
            recommendations.extend([
                "Review job description clarity - attracts right candidates faster",
                "Consider salary competitiveness analysis",
                "Evaluate recruiting sourcing channels for this role",
            ])

        return recommendations

    def _fallback_prediction(self, position: Position) -> dict:
        """Fallback prediction when model is not trained."""
        # Default heuristic: base on salary and skill count
        skill_count = len(position.required_skills) if position.required_skills else 0
        base_days = 30  # 30 day baseline
        days_to_fill = base_days + (skill_count * 5)  # Add 5 days per skill

        return {
            "days_to_fill": min(days_to_fill, 120),  # Cap at 120 days
            "confidence": 0.5,  # Low confidence for fallback
        }


__all__ = ["ForecastService"]
