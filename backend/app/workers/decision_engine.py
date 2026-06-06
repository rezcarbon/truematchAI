"""
AI-Native Auto-Decision Engine - Phase A: Autonomy Layer

Applies configurable thresholds to assessment results.
Determines: Auto-Approve, Review, or Auto-Reject.
Respects governance gate constraints.
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class DecisionThresholds:
    """Configurable decision thresholds."""

    auto_approve_score: float = 0.85  # Score >= this → Auto-Approve
    review_score_min: float = 0.65  # Score in [this, auto_approve) → Review
    auto_reject_score: float = 0.65  # Score < this → Auto-Reject (unless special flag)

    # Per-role overrides
    role_thresholds: Dict[str, Dict[str, float]] = None

    # Special flags
    force_review_if_governance_flag: bool = True
    force_review_if_consistency_outlier: bool = True
    force_review_if_coherence_fails: bool = True


class AutoDecisionEngine:
    """
    Autonomous decision engine for assessment results.

    Applies configurable thresholds to determine:
    - AUTO_APPROVE: Score high, gates passed, auto-contact recruiter
    - REVIEW: Score medium or gates flagged, requires recruiter review
    - AUTO_REJECT: Score low, candidate doesn't fit
    """

    def __init__(self, thresholds: Optional[DecisionThresholds] = None):
        self.thresholds = thresholds or DecisionThresholds()

    def _get_role_threshold(self, job: Any, role: Optional[str] = None) -> Dict[str, float]:
        """Get thresholds for specific role (if overridden)."""
        if not role or not self.thresholds.role_thresholds:
            return {
                "auto_approve": self.thresholds.auto_approve_score,
                "review_min": self.thresholds.review_score_min,
                "auto_reject": self.thresholds.auto_reject_score,
            }

        role_thresholds = self.thresholds.role_thresholds.get(role)
        if role_thresholds:
            return role_thresholds

        return {
            "auto_approve": self.thresholds.auto_approve_score,
            "review_min": self.thresholds.review_score_min,
            "auto_reject": self.thresholds.auto_reject_score,
        }

    async def decide(
        self, job: Any, assessment: Dict[str, Any], gates: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Make decision based on assessment score and governance gates.

        Returns:
            Decision: "AUTO_APPROVE", "REVIEW", or "AUTO_REJECT"
        """
        # Extract score
        score = assessment.get("capability_score", 0.0)

        # Check governance gates
        if gates:
            if not gates.get("passed", True):
                logger.warning(f"Governance gates failed for {job.job_id}, forcing REVIEW")
                return "REVIEW"

            # Check for specific gate failures
            if gates.get("coherence_failed") and self.thresholds.force_review_if_coherence_fails:
                logger.info(f"Coherence gate failed for {job.job_id}, forcing REVIEW")
                return "REVIEW"

            if gates.get("consistency_outlier") and self.thresholds.force_review_if_consistency_outlier:
                logger.info(f"Consistency outlier detected for {job.job_id}, forcing REVIEW")
                return "REVIEW"

        # Apply score-based decision
        thresholds = self._get_role_threshold(job)

        if score >= thresholds["auto_approve"]:
            logger.info(f"Auto-approve decision for {job.job_id} (score: {score:.2f})")
            return "AUTO_APPROVE"

        elif score >= thresholds["review_min"]:
            logger.info(f"Review decision for {job.job_id} (score: {score:.2f})")
            return "REVIEW"

        else:
            logger.info(f"Auto-reject decision for {job.job_id} (score: {score:.2f})")
            return "AUTO_REJECT"

    async def get_decision_reasoning(
        self, job: Any, assessment: Dict[str, Any], gates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed reasoning for the decision.

        Useful for explaining to recruiters why decision was made.
        """
        decision = await self.decide(job, assessment, gates)

        reasoning = {
            "decision": decision,
            "score": assessment.get("capability_score", 0.0),
            "keyword_score": assessment.get("keyword_score", 0.0),
            "semantic_score": assessment.get("semantic_score", 0.0),
            "thresholds": {
                "auto_approve": self.thresholds.auto_approve_score,
                "review_min": self.thresholds.review_score_min,
            },
        }

        # Add gap analysis
        if assessment.get("gaps"):
            reasoning["gaps"] = assessment["gaps"]

        # Add governance gate info
        if gates:
            reasoning["gates"] = {
                "passed": gates.get("passed", True),
                "coherence": gates.get("coherence_failed", False),
                "consistency": gates.get("consistency_outlier", False),
                "fidelity": gates.get("fidelity_concern", False),
                "bias": gates.get("bias_detected", False),
            }

        return reasoning


# Global decision engine instance
_decision_engine: Optional[AutoDecisionEngine] = None


def get_decision_engine(thresholds: Optional[DecisionThresholds] = None) -> AutoDecisionEngine:
    """Get or create decision engine."""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = AutoDecisionEngine(thresholds)
    return _decision_engine


def configure_decision_thresholds(thresholds: DecisionThresholds):
    """Configure decision thresholds (called at startup)."""
    global _decision_engine
    _decision_engine = AutoDecisionEngine(thresholds)
    logger.info(f"Decision engine configured: auto_approve={thresholds.auto_approve_score}, review={thresholds.review_score_min}")
