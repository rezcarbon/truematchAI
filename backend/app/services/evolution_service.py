"""Evolution Service - Phase 5 orchestration."""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.evolution_agent import EvolutionAgent
from app.models.hiring_outcome import HiringOutcome, HiringDecision, PerformanceRating
from app.models.candidate_match import CandidateMatch

logger = logging.getLogger("truematch.evolution_service")


class EvolutionService:
    """Service for managing hiring outcome tracking and learning.

    Responsibilities:
    - Record hiring decisions
    - Track performance outcomes
    - Process learning signals
    - Generate accuracy reports
    - Identify bias patterns
    """

    def __init__(self, db: AsyncSession):
        """Initialize evolution service.

        Args:
            db: Async database session
        """
        self.db = db
        self.agent = EvolutionAgent(db)

    async def record_hiring_decision(
        self,
        candidate_match_id: UUID,
        decision: str,
        decision_rationale: str | None = None,
        hire_date: datetime | None = None,
    ) -> HiringOutcome:
        """Record hiring decision for a candidate match.

        Args:
            candidate_match_id: Candidate match ID
            decision: Hiring decision (hired/not_hired/offer_declined/withdrawn)
            decision_rationale: Reason for decision
            hire_date: Start date if hired

        Returns:
            HiringOutcome record

        Raises:
            ValueError: If match not found
        """
        # Load candidate match
        match = await self.db.execute(
            select(CandidateMatch).where(CandidateMatch.id == candidate_match_id)
        )
        match = match.scalar_one_or_none()

        if not match:
            raise ValueError(f"Candidate match {candidate_match_id} not found")

        # Create hiring outcome
        outcome = HiringOutcome(
            candidate_match_id=match.id,
            position_id=match.position_id,
            candidate_id=match.candidate_id,
            hiring_decision=HiringDecision[decision],
            decision_made_at=datetime.utcnow(),
            decision_rationale=decision_rationale,
            hired=decision == "hired",
            hire_date=hire_date,
            match_score_at_time=match.overall_score,
        )

        self.db.add(outcome)
        await self.db.flush()

        logger.info(
            f"Recorded hiring decision for match {candidate_match_id}: {decision}"
        )

        return outcome

    async def record_performance(
        self,
        hiring_outcome_id: UUID,
        performance_rating: str,
        performance_details: dict,
        learning_feedback: dict,
    ) -> HiringOutcome:
        """Record post-hire performance evaluation.

        Args:
            hiring_outcome_id: Hiring outcome ID
            performance_rating: Performance level
            performance_details: Performance evaluation details
            learning_feedback: Feedback for learning

        Returns:
            Updated HiringOutcome record

        Raises:
            ValueError: If outcome not found
        """
        outcome = await self.db.execute(
            select(HiringOutcome).where(HiringOutcome.id == hiring_outcome_id)
        )
        outcome = outcome.scalar_one_or_none()

        if not outcome:
            raise ValueError(f"Hiring outcome {hiring_outcome_id} not found")

        outcome.performance_rating = PerformanceRating[performance_rating]
        outcome.performance_evaluated_at = datetime.utcnow()
        outcome.performance_details = performance_details
        outcome.learning_feedback = learning_feedback

        # Calculate tenure if hired
        if outcome.hire_date:
            tenure = (datetime.utcnow() - outcome.hire_date).days
            outcome.tenure_days = tenure

        await self.db.commit()

        logger.info(
            f"Recorded performance for outcome {hiring_outcome_id}: {performance_rating}"
        )

        return outcome

    async def record_retention(
        self, hiring_outcome_id: UUID, retained: bool
    ) -> HiringOutcome:
        """Record retention status.

        Args:
            hiring_outcome_id: Hiring outcome ID
            retained: Whether candidate is retained

        Returns:
            Updated HiringOutcome record

        Raises:
            ValueError: If outcome not found
        """
        outcome = await self.db.execute(
            select(HiringOutcome).where(HiringOutcome.id == hiring_outcome_id)
        )
        outcome = outcome.scalar_one_or_none()

        if not outcome:
            raise ValueError(f"Hiring outcome {hiring_outcome_id} not found")

        outcome.retained = retained
        outcome.last_active_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Updated retention for outcome {hiring_outcome_id}: {retained}")

        return outcome

    async def get_prediction_accuracy(self) -> dict:
        """Get overall prediction accuracy metrics.

        Returns:
            {
                "total_outcomes": int,
                "correct_predictions": int,
                "accuracy_rate": float,
                "by_agent": {...}
            }
        """
        # Query all outcomes with performance data
        query = select(HiringOutcome).where(HiringOutcome.performance_rating is not None)

        results = await self.db.execute(query)
        outcomes = results.scalars().all()

        if not outcomes:
            return {
                "total_outcomes": 0,
                "correct_predictions": 0,
                "accuracy_rate": 0.0,
                "by_agent": {},
            }

        total = len(outcomes)
        correct = sum(
            1
            for o in outcomes
            if o.actual_performance_vs_prediction.get("prediction_correct", False)
        )

        return {
            "total_outcomes": total,
            "correct_predictions": correct,
            "accuracy_rate": correct / total if total > 0 else 0.0,
            "by_agent": {
                "screening_accuracy": self._calculate_agent_accuracy(
                    outcomes, "screening"
                ),
                "assessment_accuracy": self._calculate_agent_accuracy(
                    outcomes, "assessment"
                ),
                "matching_accuracy": self._calculate_agent_accuracy(outcomes, "matching"),
            },
        }

    async def get_bias_report(self) -> dict:
        """Get bias analysis across hiring outcomes.

        Returns:
            {
                "total_outcomes": int,
                "suspected_bias_cases": int,
                "bias_types": {...},
                "recommendations": []
            }
        """
        # Query outcomes
        query = select(HiringOutcome)

        results = await self.db.execute(query)
        outcomes = results.scalars().all()

        if not outcomes:
            return {
                "total_outcomes": 0,
                "suspected_bias_cases": 0,
                "bias_types": {},
                "recommendations": [],
            }

        total = len(outcomes)
        bias_cases = sum(
            1 for o in outcomes if len(o.bias_signals.get("suspected_bias", [])) > 0
        )

        recommendations = []
        if bias_cases > 0:
            recommendations.append(
                f"Audit assessment bias: {bias_cases} cases with bias signals"
            )

        return {
            "total_outcomes": total,
            "suspected_bias_cases": bias_cases,
            "bias_types": {},
            "recommendations": recommendations,
        }

    def _calculate_agent_accuracy(
        self, outcomes: list[HiringOutcome], agent_type: str
    ) -> float:
        """Calculate accuracy for specific agent."""
        if agent_type == "screening":
            correct = sum(
                1
                for o in outcomes
                if o.actual_performance_vs_prediction.get("screening_accuracy", False)
            )
        elif agent_type == "assessment":
            correct = sum(
                1
                for o in outcomes
                if o.actual_performance_vs_prediction.get("assessment_accuracy", False)
            )
        else:  # matching
            correct = sum(
                1
                for o in outcomes
                if o.actual_performance_vs_prediction.get("prediction_correct", False)
            )

        return correct / len(outcomes) if outcomes else 0.0


__all__ = ["EvolutionService"]
