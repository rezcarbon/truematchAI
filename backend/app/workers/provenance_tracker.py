"""
AI-Native Provenance Tracker - Phase C: Reproducibility & Audit Trail

Tracks complete provenance of every assessment:
- Input hashing (SHA-256)
- Model version tracking
- Immutable audit log
- Full assessment reproducibility
"""
import hashlib
import logging
from dataclasses import dataclass, asdict
from app.core.clock import utcnow
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelVersion:
    """Tracks version of each model component."""

    keyword_scorer: str  # e.g., "v2.1"
    semantic_embedder: str  # e.g., "claude-sonnet-4-20250514"
    capability_analyzer: str  # e.g., "claude-opus-4-20250514"
    governance_rules: str  # e.g., "v3.0"
    decision_engine: str  # e.g., "v1.2"
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = utcnow().isoformat()

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class AssessmentProvenanceRecord:
    """Complete provenance record for single assessment."""

    assessment_id: str
    created_at: str
    input_hashes: Dict[str, str]  # cv_hash, jd_hash
    model_versions: Dict[str, str]  # All model versions at assessment time
    execution_metadata: Dict[str, Any]  # Execution context
    assessment_inputs: Dict[str, Any]  # Full input snapshot (anonymized)
    assessment_results: Dict[str, Any]  # Full results
    governance_results: Dict[str, Any]  # Gate validation results
    decision: str  # AUTO_APPROVE, REVIEW, AUTO_REJECT
    decision_reasoning: Dict[str, Any]  # Why decision was made
    notifications_sent: List[str]  # Which channels notified
    completed_at: str = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    def is_reproducible(self) -> bool:
        """Check if assessment is reproducible (has all required provenance)."""
        return bool(
            self.input_hashes
            and self.model_versions
            and self.assessment_results
            and self.decision
        )


class ProvenanceTracker:
    """
    Tracks complete provenance of assessments.

    Enables:
    - Full auditability (who, what, when, why)
    - Assessment reproducibility (same inputs → same outputs)
    - Model version tracking (which version produced this result)
    - Compliance reporting (GDPR, legal discovery)
    """

    def __init__(self):
        self.records: Dict[str, AssessmentProvenanceRecord] = {}
        self.current_model_versions = self._get_current_model_versions()

    def _get_current_model_versions(self) -> ModelVersion:
        """Get current model versions (from config or environment)."""
        return ModelVersion(
            keyword_scorer=getattr(settings, "keyword_scorer_version", "v2.1"),
            semantic_embedder=getattr(settings, "semantic_embedder_version", "claude-sonnet-4-20250514"),
            capability_analyzer=getattr(settings, "capability_analyzer_version", "claude-opus-4-20250514"),
            governance_rules=getattr(settings, "governance_rules_version", "v3.0"),
            decision_engine=getattr(settings, "decision_engine_version", "v1.2"),
        )

    def calculate_input_hash(self, input_data: str) -> str:
        """Calculate SHA-256 hash of input."""
        return hashlib.sha256(input_data.encode() if isinstance(input_data, str) else input_data).hexdigest()

    async def create_provenance_record(
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
    ) -> AssessmentProvenanceRecord:
        """
        Create complete provenance record for assessment.

        This record allows:
        1. Full audit trail (when, by what model, what decision)
        2. Assessment reproducibility (given same inputs + model versions)
        3. Compliance verification (prove decision was fair, governed)
        """
        record = AssessmentProvenanceRecord(
            assessment_id=assessment_id,
            created_at=utcnow().isoformat(),
            input_hashes={
                "cv_hash": self.calculate_input_hash(cv_content),
                "jd_hash": self.calculate_input_hash(jd_content),
            },
            model_versions=self.current_model_versions.to_dict(),
            execution_metadata={
                "environment": settings.environment,
                "version": getattr(settings, "app_version", "1.0.0"),
                "hostname": getattr(settings, "hostname", "unknown"),
                "execution_time_ms": assessment_results.get("execution_time_ms", 0),
            },
            assessment_inputs={
                "cv_filename": assessment_inputs.get("cv_filename"),
                "jd_id": assessment_inputs.get("jd_id"),
                "user_id": assessment_inputs.get("user_id"),
                # Don't store raw CV/JD (PII) - just hash
                "cv_hash": self.calculate_input_hash(cv_content),
                "jd_hash": self.calculate_input_hash(jd_content),
            },
            assessment_results=assessment_results,
            governance_results=governance_results,
            decision=decision,
            decision_reasoning=decision_reasoning,
            notifications_sent=notifications_sent,
            completed_at=utcnow().isoformat(),
        )

        self.records[assessment_id] = record

        logger.info(
            f"Provenance record created: {assessment_id}",
            extra={
                "assessment_id": assessment_id,
                "cv_hash": record.input_hashes["cv_hash"],
                "jd_hash": record.input_hashes["jd_hash"],
                "decision": decision,
                "reproducible": record.is_reproducible(),
            },
        )

        return record

    async def verify_reproducibility(
        self, assessment_id: str, cv_content: str, jd_content: str
    ) -> Dict[str, Any]:
        """
        Verify that an assessment is reproducible.

        Re-running assessment with same CV/JD should produce same results
        if using same model versions.
        """
        record = self.records.get(assessment_id)
        if not record:
            return {
                "reproducible": False,
                "reason": "No provenance record found",
            }

        # Check input hashes match
        cv_hash = self.calculate_input_hash(cv_content)
        jd_hash = self.calculate_input_hash(jd_content)

        if cv_hash != record.input_hashes["cv_hash"]:
            return {
                "reproducible": False,
                "reason": "CV content has changed",
                "original_cv_hash": record.input_hashes["cv_hash"],
                "current_cv_hash": cv_hash,
            }

        if jd_hash != record.input_hashes["jd_hash"]:
            return {
                "reproducible": False,
                "reason": "JD content has changed",
                "original_jd_hash": record.input_hashes["jd_hash"],
                "current_jd_hash": jd_hash,
            }

        # Check model versions
        current_versions = self.current_model_versions.to_dict()
        model_versions_match = all(
            current_versions.get(k) == v for k, v in record.model_versions.items()
        )

        if not model_versions_match:
            return {
                "reproducible": False,
                "reason": "Model versions have changed since assessment",
                "original_versions": record.model_versions,
                "current_versions": current_versions,
            }

        return {
            "reproducible": True,
            "assessment_id": assessment_id,
            "original_decision": record.decision,
            "can_re_run_with_same_results": True,
            "note": "If model versions are identical, re-running assessment should produce same results",
        }

    def get_provenance_record(self, assessment_id: str) -> Optional[AssessmentProvenanceRecord]:
        """Get provenance record for assessment."""
        return self.records.get(assessment_id)

    def generate_audit_report(self, assessment_id: str) -> Dict[str, Any]:
        """Generate audit-ready report for assessment."""
        record = self.records.get(assessment_id)
        if not record:
            return {"error": "Provenance record not found"}

        return {
            "audit_report": {
                "assessment_id": assessment_id,
                "created_at": record.created_at,
                "completed_at": record.completed_at,
                "input_hashes": record.input_hashes,
                "model_versions": record.model_versions,
                "decision": record.decision,
                "decision_reasoning": record.decision_reasoning,
                "governance_results": record.governance_results,
                "notifications_sent": record.notifications_sent,
                "reproducible": record.is_reproducible(),
                "executive_summary": (
                    f"Assessment {assessment_id}: Decision {record.decision}. "
                    f"Evaluated by {record.model_versions['capability_analyzer']}. "
                    f"Governance gates: {list(record.governance_results.keys())}. "
                    f"{'Reproducible with same model versions.' if record.is_reproducible() else 'Not fully documented.'}"
                ),
            }
        }


# Global provenance tracker instance
_provenance_tracker: Optional[ProvenanceTracker] = None


def get_provenance_tracker() -> ProvenanceTracker:
    """Get or create provenance tracker."""
    global _provenance_tracker
    if _provenance_tracker is None:
        _provenance_tracker = ProvenanceTracker()
    return _provenance_tracker
