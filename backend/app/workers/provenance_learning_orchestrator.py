"""
AI-Native Provenance & Learning Orchestrator - Phase C+D Integration

Unifies provenance tracking (Phase C) and learning loop integration (Phase D).
Creates complete audit trail while automatically learning from feedback.
"""
import logging
from typing import Any, Dict, List, Optional

from app.workers.audit_trail import AuditEvent, ImmutableAuditTrail, get_audit_trail
from app.workers.learning_loop import LearningLoopIntegrator, get_learning_loop
from app.workers.provenance_tracker import (
    AssessmentProvenanceRecord,
    ProvenanceTracker,
    get_provenance_tracker,
)

logger = logging.getLogger(__name__)


class ProvenanceLearningOrchestrator:
    """
    Unified orchestrator for Phase C (Provenance) and Phase D (Learning).

    Responsibilities:
    1. Create provenance records with full input hashing
    2. Log immutable audit trail of all operations
    3. Process training feedback
    4. Update capability weights
    5. Schedule and perform recalibration
    6. Batch re-score candidates with new weights
    """

    def __init__(
        self,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        audit_trail: Optional[ImmutableAuditTrail] = None,
        learning_loop: Optional[LearningLoopIntegrator] = None,
    ):
        self.provenance = provenance_tracker or get_provenance_tracker()
        self.audit = audit_trail or get_audit_trail()
        self.learning = learning_loop or get_learning_loop()

    async def create_full_provenance_record(
        self,
        assessment_id: str,
        cv_content: str,
        jd_content: str,
        assessment_inputs: Dict[str, Any],
        assessment_results: Dict[str, Any],
        governance_results: Dict[str, Any],
        decision: str,
        decision_reasoning: Dict[str, Any],
        notifications_sent: List[str],
        actor: str = "system",
    ) -> Dict[str, Any]:
        """
        Create complete provenance record with audit trail.

        This creates:
        1. Provenance record (SHA-256 hashes, model versions)
        2. Audit event for assessment completion
        """
        # Create provenance record
        provenance_record = await self.provenance.create_provenance_record(
            assessment_id=assessment_id,
            cv_content=cv_content,
            jd_content=jd_content,
            assessment_inputs=assessment_inputs,
            assessment_results=assessment_results,
            governance_results=governance_results,
            decision=decision,
            decision_reasoning=decision_reasoning,
            notifications_sent=notifications_sent,
        )

        # Log audit event
        await self.audit.log_assessment_completed(
            assessment_id=assessment_id,
            final_decision=decision,
            processing_time_ms=assessment_results.get("execution_time_ms", 0),
        )

        logger.info(
            f"Full provenance record created: {assessment_id}",
            extra={
                "reproducible": provenance_record.is_reproducible(),
                "decision": decision,
            },
        )

        return {
            "assessment_id": assessment_id,
            "provenance_record": provenance_record.to_dict(),
            "reproducible": provenance_record.is_reproducible(),
        }

    async def process_training_and_learn(
        self,
        feedback_type: str,
        feedback_data: Dict[str, Any],
        source: str = "chat",  # chat, upload, api
    ) -> Dict[str, Any]:
        """
        Process training feedback and update learning system.

        Integrates feedback into capability weights and credential mappings.
        """
        result = await self.learning.process_training_feedback(feedback_type, feedback_data)

        logger.info(
            f"Training feedback processed and learned",
            extra={
                "feedback_type": feedback_type,
                "source": source,
                "result": result.get("processed", False),
            },
        )

        return {
            "feedback_type": feedback_type,
            "learned": result,
            "learning_metrics": self.learning.get_learning_metrics(),
        }

    async def get_assessment_reproducibility(
        self, assessment_id: str, cv_content: str, jd_content: str
    ) -> Dict[str, Any]:
        """
        Check if assessment is reproducible.

        Verifies that re-running with same inputs and model versions
        would produce same results.
        """
        reproducibility = await self.provenance.verify_reproducibility(
            assessment_id, cv_content, jd_content
        )

        logger.info(
            f"Reproducibility check: {assessment_id}",
            extra={
                "reproducible": reproducibility.get("reproducible", False),
            },
        )

        return reproducibility

    async def generate_compliance_package(self, assessment_id: str) -> Dict[str, Any]:
        """
        Generate complete compliance package for assessment.

        Includes:
        - Provenance record (for reproducibility)
        - Audit trail (for legal discovery)
        - Decision reasoning (for explainability)
        """
        # Get provenance record
        provenance = self.provenance.get_provenance_record(assessment_id)
        if not provenance:
            return {"error": "Provenance record not found"}

        # Get audit history
        audit_events = await self.audit.get_assessment_history(assessment_id)

        # Generate reports
        provenance_report = self.provenance.generate_audit_report(assessment_id)
        compliance_report = await self.audit.generate_compliance_report(assessment_id)

        logger.info(
            f"Compliance package generated: {assessment_id}",
            extra={
                "audit_events": len(audit_events),
                "reproducible": provenance.is_reproducible(),
            },
        )

        return {
            "assessment_id": assessment_id,
            "provenance_report": provenance_report,
            "compliance_report": compliance_report,
            "audit_events_count": len(audit_events),
            "reproducible": provenance.is_reproducible(),
        }

    async def schedule_learning_recalibration(self, interval_hours: int = 24):
        """Schedule automatic recalibration of learning weights."""
        await self.learning.schedule_recalibration(interval_hours)

        logger.info(
            f"Learning recalibration scheduled every {interval_hours} hours"
        )

    async def perform_learning_recalibration(
        self,
        assessment_executor: callable,
        holdout_assessments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform recalibration and validate learning improvements.

        Tests new weights against holdout assessment set.
        """
        result = await self.learning.perform_recalibration(
            assessment_executor, holdout_assessments
        )

        logger.info(
            f"Learning recalibration completed",
            extra={
                "improvement": result.get("improvement", 0),
                "rolled_back": result.get("weights_rolled_back", False),
            },
        )

        return result

    async def batch_rescore_with_learning(
        self,
        candidate_assessments: List[Dict[str, Any]],
        executor: callable,
    ) -> Dict[str, Any]:
        """
        Batch re-score candidates using updated learning weights.

        Allows recruiters to see impact of new learned patterns.
        """
        result = await self.learning.batch_rescore_candidates(
            candidate_assessments, executor
        )

        logger.info(
            f"Batch re-scoring with learning completed",
            extra={
                "total_rescored": result.get("total_rescored"),
                "decisions_changed": result.get("decisions_changed"),
            },
        )

        return result

    def get_system_state(self) -> Dict[str, Any]:
        """Get complete system state: provenance, audit, learning."""
        return {
            "provenance": {
                "records_created": len(self.provenance.records),
            },
            "audit": {
                "events_logged": len(self.audit.events),
                "assessments_tracked": len(self.audit.assessment_events),
            },
            "learning": self.learning.get_learning_metrics(),
        }


# Global orchestrator instance
_orchestrator: Optional[ProvenanceLearningOrchestrator] = None


def get_provenance_learning_orchestrator() -> ProvenanceLearningOrchestrator:
    """Get or create provenance+learning orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ProvenanceLearningOrchestrator(
            provenance_tracker=get_provenance_tracker(),
            audit_trail=get_audit_trail(),
            learning_loop=get_learning_loop(),
        )
    return _orchestrator
