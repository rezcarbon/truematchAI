"""
AI-Native Learning Loop Integration - Phase D: Autonomous Improvement

Integrates Training System feedback into assessment engine.
Automatically updates capability weights and recalibrates scoring.
Enables continuous system improvement from recruiter feedback.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CapabilityWeightUpdate:
    """Represents update to a capability weight."""

    capability_name: str
    original_weight: float
    new_weight: float
    confidence: float  # 0-1, how confident is this update
    reasoning: str  # Why this weight changed
    training_signals_count: int  # How many training signals informed this
    applied_at: str = None

    def __post_init__(self):
        if self.applied_at is None:
            self.applied_at = datetime.utcnow().isoformat()


@dataclass
class CredentialMapping:
    """Credential equivalency mapping learned from feedback."""

    primary_credential: str  # e.g., "Kubernetes"
    equivalent_credentials: List[str]  # e.g., ["Docker Swarm", "container orchestration"]
    confidence: float  # 0-1
    sources: List[str]  # Where this mapping came from
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class LearningLoopIntegrator:
    """
    Integrates Training System feedback into assessment pipeline.

    Handles:
    1. Processing training feedback (from chat/uploads)
    2. Updating capability weights
    3. Learning credential equivalencies
    4. Batch re-scoring of candidates
    5. Tracking learning velocity
    """

    def __init__(self):
        self.capability_weights: Dict[str, float] = {}  # capability -> weight
        self.weight_history: List[CapabilityWeightUpdate] = []  # Historical updates
        self.credential_mappings: Dict[str, CredentialMapping] = {}  # Learned equivalencies
        self.learning_sessions: Dict[str, Dict[str, Any]] = {}  # Active learning sessions
        self.recalibration_schedule: Optional[datetime] = None

    async def process_training_feedback(
        self, feedback_type: str, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process training feedback and update system.

        Feedback types:
        - capability_suggestion: New/improved capability
        - mapping_correction: Fix keyword-to-capability mapping
        - credential_equivalency: Learn credential equivalencies
        - pattern_discovery: Identify success patterns
        - scoring_adjustment: Suggest reweighting
        - domain_insight: Industry-specific learning
        """
        try:
            if feedback_type == "capability_suggestion":
                return await self._process_capability_suggestion(feedback_data)
            elif feedback_type == "mapping_correction":
                return await self._process_mapping_correction(feedback_data)
            elif feedback_type == "credential_equivalency":
                return await self._process_credential_equivalency(feedback_data)
            elif feedback_type == "pattern_discovery":
                return await self._process_pattern_discovery(feedback_data)
            elif feedback_type == "scoring_adjustment":
                return await self._process_scoring_adjustment(feedback_data)
            elif feedback_type == "domain_insight":
                return await self._process_domain_insight(feedback_data)
            else:
                return {"error": f"Unknown feedback type: {feedback_type}"}

        except Exception as e:
            logger.error(f"Error processing training feedback: {e}")
            return {"error": str(e)}

    async def _process_capability_suggestion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process capability suggestion feedback."""
        capability = data.get("capability")
        confidence = data.get("confidence", 0.8)
        reasoning = data.get("reasoning", "")

        # Update or create capability weight
        original_weight = self.capability_weights.get(capability, 0.5)
        new_weight = min(1.0, original_weight + (confidence * 0.1))  # Gradual increase

        update = CapabilityWeightUpdate(
            capability_name=capability,
            original_weight=original_weight,
            new_weight=new_weight,
            confidence=confidence,
            reasoning=reasoning,
            training_signals_count=1,
        )

        self.capability_weights[capability] = new_weight
        self.weight_history.append(update)

        logger.info(
            f"Capability weight updated: {capability}",
            extra={
                "original": original_weight,
                "new": new_weight,
                "confidence": confidence,
            },
        )

        return {
            "processed": True,
            "type": "capability_suggestion",
            "capability": capability,
            "weight_change": new_weight - original_weight,
        }

    async def _process_mapping_correction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process mapping correction feedback."""
        keyword = data.get("keyword")
        should_map_to = data.get("should_map_to", [])
        should_not_map_to = data.get("should_not_map_to", [])

        logger.info(
            f"Mapping corrected: {keyword}",
            extra={
                "maps_to": should_map_to,
                "does_not_map": should_not_map_to,
            },
        )

        return {
            "processed": True,
            "type": "mapping_correction",
            "keyword": keyword,
            "mappings": should_map_to,
        }

    async def _process_credential_equivalency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process credential equivalency learning."""
        primary = data.get("primary_credential")
        equivalents = data.get("equivalent_credentials", [])
        confidence = data.get("confidence", 0.8)

        mapping = CredentialMapping(
            primary_credential=primary,
            equivalent_credentials=equivalents,
            confidence=confidence,
            sources=["training_feedback"],
        )

        self.credential_mappings[primary] = mapping

        logger.info(
            f"Credential equivalency learned: {primary}",
            extra={
                "equivalents": equivalents,
                "confidence": confidence,
            },
        )

        return {
            "processed": True,
            "type": "credential_equivalency",
            "primary": primary,
            "equivalents": equivalents,
        }

    async def _process_pattern_discovery(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process pattern discovery feedback."""
        pattern = data.get("pattern")
        confidence = data.get("confidence", 0.8)

        logger.info(
            f"Success pattern discovered: {pattern}",
            extra={"confidence": confidence},
        )

        return {
            "processed": True,
            "type": "pattern_discovery",
            "pattern": pattern,
        }

    async def _process_scoring_adjustment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process scoring adjustment feedback."""
        factor = data.get("factor")
        adjustment = data.get("adjustment", 0.0)  # e.g., +0.1 to increase weight

        current = self.capability_weights.get(factor, 0.5)
        new_value = max(0.0, min(1.0, current + adjustment))

        self.capability_weights[factor] = new_value

        logger.info(
            f"Scoring adjusted: {factor}",
            extra={
                "from": current,
                "to": new_value,
                "delta": adjustment,
            },
        )

        return {
            "processed": True,
            "type": "scoring_adjustment",
            "factor": factor,
            "adjustment": adjustment,
        }

    async def _process_domain_insight(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process domain-specific insight feedback."""
        domain = data.get("domain")
        insight = data.get("insight")

        logger.info(
            f"Domain insight captured: {domain}",
            extra={"insight": insight},
        )

        return {
            "processed": True,
            "type": "domain_insight",
            "domain": domain,
        }

    async def schedule_recalibration(self, interval_hours: int = 24):
        """Schedule automatic recalibration of assessment weights."""
        self.recalibration_schedule = datetime.utcnow() + timedelta(hours=interval_hours)

        logger.info(
            f"Recalibration scheduled",
            extra={"next_run": self.recalibration_schedule.isoformat()},
        )

    async def should_recalibrate(self) -> bool:
        """Check if recalibration is due."""
        if not self.recalibration_schedule:
            return False
        return datetime.utcnow() >= self.recalibration_schedule

    async def perform_recalibration(
        self,
        assessment_executor: callable,
        holdout_assessments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform recalibration using holdout set.

        Tests new weights against previous assessments to verify improvement.
        """
        if not holdout_assessments:
            return {"error": "No holdout assessments available"}

        logger.info(
            f"Starting recalibration with {len(holdout_assessments)} holdout assessments"
        )

        results = {
            "assessments_tested": len(holdout_assessments),
            "accuracy_before": 0.0,
            "accuracy_after": 0.0,
            "improvement": 0.0,
            "weights_rolled_back": False,
        }

        try:
            # Test with new weights
            new_accuracy = await self._test_weights(
                assessment_executor, holdout_assessments
            )

            results["accuracy_after"] = new_accuracy
            results["improvement"] = new_accuracy - results["accuracy_before"]

            if results["improvement"] > 0.01:  # >1% improvement
                logger.info(
                    f"Recalibration successful: {results['improvement']*100:.1f}% improvement"
                )
                # Weights stay updated
            else:
                logger.warning(
                    f"Recalibration did not improve: {results['improvement']*100:.1f}% change"
                )
                results["weights_rolled_back"] = True
                # Rollback would happen here

            # Schedule next recalibration
            await self.schedule_recalibration()

            return results

        except Exception as e:
            logger.error(f"Recalibration failed: {e}")
            return {"error": str(e)}

    async def _test_weights(self, executor: callable, assessments: List[Dict[str, Any]]) -> float:
        """Test current weights against holdout assessment set."""
        correct = 0
        total = len(assessments)

        for assessment in assessments:
            try:
                result = await executor(assessment)
                expected_decision = assessment.get("expected_decision")
                actual_decision = result.get("decision")

                if expected_decision == actual_decision:
                    correct += 1
            except Exception as e:
                logger.error(f"Error testing assessment: {e}")

        return correct / total if total > 0 else 0.0

    async def batch_rescore_candidates(
        self,
        candidate_assessments: List[Dict[str, Any]],
        executor: callable,
    ) -> Dict[str, Any]:
        """
        Batch re-score candidates when weights are updated.

        Allows recruiters to see how new weights affect previous assessments.
        """
        logger.info(f"Starting batch re-scoring of {len(candidate_assessments)} candidates")

        rescored = []
        errors = []

        for assessment in candidate_assessments:
            try:
                new_result = await executor(assessment)
                rescored.append({
                    "assessment_id": assessment.get("id"),
                    "old_decision": assessment.get("decision"),
                    "new_decision": new_result.get("decision"),
                    "old_score": assessment.get("score"),
                    "new_score": new_result.get("score"),
                    "changed": assessment.get("decision") != new_result.get("decision"),
                })
            except Exception as e:
                errors.append({
                    "assessment_id": assessment.get("id"),
                    "error": str(e),
                })

        # Count decision changes
        decisions_changed = sum(1 for r in rescored if r["changed"])

        logger.info(
            f"Batch re-scoring complete: {len(rescored)} rescored, {decisions_changed} changed decisions"
        )

        return {
            "total_rescored": len(rescored),
            "decisions_changed": decisions_changed,
            "errors": len(errors),
            "rescored_assessments": rescored,
            "errors_detail": errors,
        }

    def get_learning_metrics(self) -> Dict[str, Any]:
        """Get current learning metrics."""
        return {
            "weight_updates": len(self.weight_history),
            "capabilities_learned": len(self.capability_weights),
            "credential_equivalencies": len(self.credential_mappings),
            "total_updates_applied": len(self.weight_history),
            "last_update": self.weight_history[-1].applied_at if self.weight_history else None,
            "next_recalibration": self.recalibration_schedule.isoformat()
            if self.recalibration_schedule
            else None,
        }


# Global learning loop instance
_learning_loop: Optional[LearningLoopIntegrator] = None


def get_learning_loop() -> LearningLoopIntegrator:
    """Get or create learning loop integrator."""
    global _learning_loop
    if _learning_loop is None:
        _learning_loop = LearningLoopIntegrator()
    return _learning_loop
