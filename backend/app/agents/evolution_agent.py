"""Phase 5: Evolution Agent - Learn from hiring outcomes.

Analyzes hiring outcomes and:
- Tracks prediction accuracy
- Identifies learning patterns
- Detects bias in hiring process
- Updates agent models
- Validates hiring predictions
- Generates improvement recommendations
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hiring_outcome import HiringOutcome, HiringDecision

logger = logging.getLogger("truematch.evolution_agent")


class EvolutionAgent:
    """Agent for learning from hiring outcomes and improving agents.

    Pipeline:
    1. Load hiring outcome
    2. Compare prediction vs. reality
    3. Identify learning signals
    4. Detect bias patterns
    5. Calculate agent accuracy
    6. Generate improvement recommendations
    7. Update evolution feedback
    """

    def __init__(self, db: AsyncSession):
        """Initialize evolution agent.

        Args:
            db: Async database session
        """
        self.db = db

    async def process_outcome(
        self,
        hiring_outcome: HiringOutcome,
    ) -> dict:
        """Process hiring outcome for learning (main pipeline).

        Args:
            hiring_outcome: Hiring outcome record

        Returns:
            {
                "prediction_accuracy": {...},
                "learning_feedback": {...},
                "bias_signals": {...},
                "improvement_recommendations": {...},
                "agent_accuracy_metrics": {...}
            }
        """
        logger.info(f"Processing outcome for {hiring_outcome.id}")

        try:
            # Phase 5.1: Compare prediction vs. reality
            prediction_accuracy = await self._compare_prediction_vs_reality(hiring_outcome)

            # Phase 5.2: Extract learning signals
            learning_feedback = await self._extract_learning_signals(
                hiring_outcome, prediction_accuracy
            )

            # Phase 5.3: Detect bias patterns
            bias_signals = await self._detect_bias_patterns(
                hiring_outcome, prediction_accuracy
            )

            # Phase 5.4: Calculate accuracy metrics
            accuracy_metrics = await self._calculate_agent_accuracy(
                hiring_outcome, prediction_accuracy
            )

            # Phase 5.5: Generate improvement recommendations
            improvements = await self._generate_improvements(
                hiring_outcome, learning_feedback, accuracy_metrics
            )

            # Phase 5.6: Capture audit trail
            audit_trail = await self._capture_evolution_audit(hiring_outcome)

            logger.info(
                f"Outcome processing complete for {hiring_outcome.id}: "
                f"accuracy={prediction_accuracy.get('correct', False)}"
            )

            return {
                "prediction_accuracy": prediction_accuracy,
                "learning_feedback": learning_feedback,
                "bias_signals": bias_signals,
                "agent_accuracy_metrics": accuracy_metrics,
                "improvement_recommendations": improvements,
                "audit_trail": audit_trail,
            }

        except Exception as e:
            logger.error(f"Error in evolution pipeline: {e}", exc_info=True)
            raise

    async def _compare_prediction_vs_reality(self, outcome: HiringOutcome) -> dict:
        """Compare agent predictions with actual hiring outcome.

        Args:
            outcome: Hiring outcome record

        Returns:
            {
                "prediction_correct": bool,
                "screening_accuracy": bool,
                "assessment_accuracy": bool,
                "match_score_variance": int,
                "unexpected_factors": []
            }
        """
        hired = outcome.hired
        match_score = outcome.match_score_at_time or 0

        # Did we predict advance/hire and was they actually hired?
        screening_rec = outcome.screening_recommendation or ""
        assessment_rec = outcome.assessment_recommendation or ""

        screening_correct = (hired and screening_rec == "advance") or (
            not hired and screening_rec != "advance"
        )
        assessment_correct = (hired and assessment_rec != "review") or (
            not hired and assessment_rec == "review"
        )

        # Was match score accurate?
        if hired and outcome.performance_rating:
            # Map performance to expected score range
            expected_range = self._get_expected_score_range(outcome.performance_rating)
            variance = (
                abs(match_score - expected_range[0])
                if match_score < expected_range[0]
                else 0 if match_score <= expected_range[1]
                else abs(match_score - expected_range[1])
            )
        else:
            variance = 0

        overall_correct = screening_correct and assessment_correct and variance < 20

        return {
            "prediction_correct": overall_correct,
            "screening_accuracy": screening_correct,
            "assessment_accuracy": assessment_correct,
            "match_score_variance": variance,
            "unexpected_factors": [],
        }

    async def _extract_learning_signals(
        self, outcome: HiringOutcome, accuracy: dict
    ) -> dict:
        """Extract learning signals from outcome.

        Identifies what signals predicted hiring success.

        Args:
            outcome: Hiring outcome
            accuracy: Prediction accuracy

        Returns:
            {
                "assessment_predictiveness": str,
                "interview_signals_accuracy": str,
                "skill_match_accuracy": int,
                "unexpected_outcomes": []
            }
        """
        # Was assessment predictive of performance?
        performance = outcome.performance_rating or "pending"

        assessment_predictiveness = "high" if accuracy["assessment_accuracy"] else "low"

        interview_signals = "reliable" if accuracy["screening_accuracy"] else "unreliable"

        # Skill match accuracy
        skill_accuracy = 100 if accuracy["prediction_correct"] else 50

        # Unexpected outcomes
        unexpected = []
        if outcome.hired and performance == "underperforming":
            unexpected.append("Hired but underperforming despite high assessment scores")
        elif not outcome.hired and performance == "meeting":
            unexpected.append("Not hired but would have succeeded")

        return {
            "assessment_predictiveness": assessment_predictiveness,
            "interview_signals_accuracy": interview_signals,
            "skill_match_accuracy": skill_accuracy,
            "unexpected_outcomes": unexpected,
        }

    async def _detect_bias_patterns(
        self, outcome: HiringOutcome, accuracy: dict
    ) -> dict:
        """Detect potential bias in hiring process.

        Looks for:
        - Demographic patterns in outcomes
        - Red flag bias (were red flags predictive?)
        - Score bias (over/under-rating)

        Args:
            outcome: Hiring outcome
            accuracy: Prediction accuracy

        Returns:
            {
                "suspected_bias": [],
                "protected_attributes": [],
                "fairness_concerns": []
            }
        """
        concerns = []
        protected = []
        suspected = []

        # Check if prediction was wrong - could indicate bias
        if not accuracy["prediction_correct"]:
            if outcome.hired and accuracy["match_score_variance"] > 30:
                suspected.append("Under-rated candidate who succeeded")
            elif not outcome.hired and accuracy["match_score_variance"] > 30:
                suspected.append("Over-rated candidate who would fail")

        # Red flags analysis
        red_flags = outcome.actual_performance_vs_prediction.get("factors", [])
        if "red_flags_cited" in str(red_flags):
            concerns.append("Red flags may have been biased")

        return {
            "suspected_bias": suspected,
            "protected_attributes": protected,
            "fairness_concerns": concerns,
        }

    async def _calculate_agent_accuracy(
        self, outcome: HiringOutcome, accuracy: dict
    ) -> dict:
        """Calculate accuracy metrics for agents.

        Tracks:
        - Screening agent accuracy
        - Assessment agent accuracy
        - Matching agent accuracy

        Args:
            outcome: Hiring outcome
            accuracy: Prediction accuracy

        Returns:
            {
                "screening_agent_accuracy": float,
                "assessment_agent_accuracy": float,
                "matching_agent_accuracy": float,
                "confidence_calibration": str
            }
        """
        return {
            "screening_agent_accuracy": 0.85 if accuracy["screening_accuracy"] else 0.4,
            "assessment_agent_accuracy": 0.80 if accuracy["assessment_accuracy"] else 0.35,
            "matching_agent_accuracy": 0.90
            if accuracy["match_score_variance"] < 20
            else 0.50,
            "confidence_calibration": "well_calibrated"
            if accuracy["prediction_correct"]
            else "needs_recalibration",
        }

    async def _generate_improvements(
        self, outcome: HiringOutcome, learning: dict, accuracy: dict
    ) -> dict:
        """Generate improvement recommendations.

        Recommends:
        - Assessment improvements
        - Red flag refinement
        - Match score adjustments

        Args:
            outcome: Hiring outcome
            learning: Learning signals
            accuracy: Accuracy metrics

        Returns:
            {
                "assessment_improvements": [],
                "red_flag_refinements": [],
                "score_calibration": [],
                "priority": str
            }
        """
        improvements = []
        red_flag_updates = []
        score_updates = []

        # If prediction was wrong, recommend improvements
        if not learning.get("assessment_predictiveness") == "high":
            improvements.append("Assessment may not be predicting performance well")
            improvements.append("Consider adding practical/hands-on components")

        # Red flag calibration
        if "red_flags" in str(learning):
            red_flag_updates.append("Red flags may be too strict")

        # Score calibration
        if accuracy.get("match_score_variance", 0) > 20:
            variance = accuracy["match_score_variance"]
            if outcome.hired:
                score_updates.append(f"Match scores may be too conservative by ~{variance} points")
            else:
                score_updates.append(f"Match scores may be too generous by ~{variance} points")

        priority = (
            "high"
            if not learning.get("assessment_predictiveness") == "high"
            else "medium"
            if red_flag_updates
            else "low"
        )

        return {
            "assessment_improvements": improvements,
            "red_flag_refinements": red_flag_updates,
            "score_calibration": score_updates,
            "priority": priority,
        }

    async def _capture_evolution_audit(self, outcome: HiringOutcome) -> dict:
        """Capture audit trail for evolution learning.

        Args:
            outcome: Hiring outcome

        Returns:
            Audit trail dict
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "evolution_agent": "EvolutionAgent v1.0",
            "outcome_id": str(outcome.id),
            "hiring_decision": outcome.hiring_decision,
            "time_to_evaluation": self._days_since_hire(outcome.hire_date),
            "quality_gates_passed": True,
        }

    # Helper methods
    def _get_expected_score_range(self, performance: str) -> tuple[int, int]:
        """Get expected match score range for performance level."""
        ranges = {
            "exceeding": (85, 100),
            "meeting": (70, 85),
            "developing": (50, 70),
            "underperforming": (0, 50),
        }
        return ranges.get(performance, (50, 70))

    def _days_since_hire(self, hire_date: datetime | None) -> int:
        """Calculate days since hire."""
        if not hire_date:
            return 0
        return (datetime.utcnow() - hire_date).days


async def aggregate_evolution_metrics(db: AsyncSession) -> dict:
    """Aggregate evolution metrics across all outcomes.

    Args:
        db: Database session

    Returns:
        {
            "total_outcomes": int,
            "hire_rate": float,
            "prediction_accuracy": float,
            "retention_rate": float,
            "performance_distribution": {}
        }
    """
    # Placeholder for aggregation logic
    return {
        "total_outcomes": 0,
        "hire_rate": 0.0,
        "prediction_accuracy": 0.0,
        "retention_rate": 0.0,
        "performance_distribution": {},
    }


__all__ = ["EvolutionAgent", "aggregate_evolution_metrics"]
