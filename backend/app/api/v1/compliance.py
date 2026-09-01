"""
Compliance & Provenance Reporting API - Phase C+D

Endpoints for:
- Provenance record retrieval
- Audit trail access
- Reproducibility verification
- Compliance package generation
- Learning metrics
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from app.workers.provenance_learning_orchestrator import (
    get_provenance_learning_orchestrator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/assessment/{assessment_id}/provenance")
async def get_assessment_provenance(assessment_id: str) -> Dict[str, Any]:
    """
    Get provenance record for assessment.

    Includes:
    - Input hashes (SHA-256)
    - Model versions
    - Execution metadata
    - Assessment results
    - Governance results
    - Decision and reasoning
    - Reproducibility status
    """
    orchestrator = get_provenance_learning_orchestrator()
    provenance = orchestrator.provenance.get_provenance_record(assessment_id)

    if not provenance:
        raise HTTPException(status_code=404, detail="Provenance record not found")

    return {
        "assessment_id": assessment_id,
        "provenance": provenance.to_dict(),
        "reproducible": provenance.is_reproducible(),
    }


@router.get("/assessment/{assessment_id}/audit-trail")
async def get_assessment_audit_trail(assessment_id: str) -> Dict[str, Any]:
    """
    Get complete audit trail for assessment.

    Shows all operations with timestamps and results:
    - ASSESSMENT_CREATED
    - ASSESSMENT_STARTED
    - GATES_VALIDATED
    - DECISION_MADE
    - NOTIFIED
    - COMPLETED/FAILED
    """
    orchestrator = get_provenance_learning_orchestrator()

    try:
        events = await orchestrator.audit.get_assessment_history(assessment_id)
    except Exception as e:
        logger.error(f"Error retrieving audit trail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")

    if not events:
        raise HTTPException(status_code=404, detail="No audit trail found for assessment")

    return {
        "assessment_id": assessment_id,
        "event_count": len(events),
        "events": [e.to_dict() for e in events],
    }


@router.get("/assessment/{assessment_id}/compliance-package")
async def get_compliance_package(assessment_id: str) -> Dict[str, Any]:
    """
    Generate complete compliance package for assessment.

    Includes:
    - Provenance report (input hashes, model versions, reproducibility)
    - Audit trail (complete event history)
    - Governance validation results
    - Decision reasoning
    - Compliance summary

    Use for:
    - Legal discovery
    - Regulatory audits
    - Dispute resolution
    - GDPR compliance verification
    """
    orchestrator = get_provenance_learning_orchestrator()

    try:
        package = await orchestrator.generate_compliance_package(assessment_id)
    except Exception as e:
        logger.error(f"Error generating compliance package: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate compliance package"
        )

    if "error" in package:
        raise HTTPException(status_code=404, detail=package["error"])

    return package


@router.post("/assessment/{assessment_id}/verify-reproducibility")
async def verify_reproducibility(
    assessment_id: str, cv_content: str, jd_content: str
) -> Dict[str, Any]:
    """
    Verify that assessment is reproducible.

    Tests whether re-running the assessment with the same CV and JD content
    would produce the same results, given the same model versions.

    Returns:
    - reproducible: bool (true if same inputs + same models = same outputs)
    - reason: str (if not reproducible, why)
    - original_versions vs current_versions (if model versions changed)
    """
    orchestrator = get_provenance_learning_orchestrator()

    try:
        result = await orchestrator.get_assessment_reproducibility(
            assessment_id=assessment_id,
            cv_content=cv_content,
            jd_content=jd_content,
        )
    except Exception as e:
        logger.error(f"Error verifying reproducibility: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify reproducibility")

    return result


@router.get("/assessments/audit-export")
async def export_audit_log(assessment_ids: list[str] = Query(...)) -> Dict[str, Any]:
    """
    Export audit log in JSON-lines format.

    Returns one event per line for integration with legal discovery tools.

    Query parameters:
    - assessment_ids: List of assessment IDs to export
    """
    if not assessment_ids:
        raise HTTPException(
            status_code=400, detail="At least one assessment ID required"
        )

    orchestrator = get_provenance_learning_orchestrator()

    try:
        audit_log = await orchestrator.audit.export_audit_log(assessment_ids)
    except Exception as e:
        logger.error(f"Error exporting audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to export audit log")

    return {
        "assessment_ids": assessment_ids,
        "event_count": len(audit_log.split("\n")),
        "format": "json-lines",
        "audit_log": audit_log,
    }


@router.get("/learning/metrics")
async def get_learning_metrics() -> Dict[str, Any]:
    """
    Get current learning system metrics.

    Returns:
    - weight_updates: Number of weight updates applied
    - capabilities_learned: Number of unique capabilities tracked
    - credential_equivalencies: Number of credential equivalencies learned
    - total_updates_applied: Total updates in system
    - last_update: When was the last weight update
    - next_recalibration: When is the next recalibration scheduled
    """
    orchestrator = get_provenance_learning_orchestrator()
    metrics = orchestrator.learning.get_learning_metrics()

    return {
        "learning_metrics": metrics,
        "learning_enabled": True,
    }


@router.post("/learning/process-feedback")
async def process_training_feedback(
    feedback_type: str, feedback_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process training feedback to update learning system.

    Feedback types:
    - capability_suggestion: Suggest weight for a capability
    - mapping_correction: Correct keyword->capability mapping
    - credential_equivalency: Learn credential equivalencies
    - pattern_discovery: Record success patterns
    - scoring_adjustment: Adjust weights directly
    - domain_insight: Record domain-specific insights

    Example (capability_suggestion):
    ```json
    {
        "feedback_type": "capability_suggestion",
        "feedback_data": {
            "capability": "System Design",
            "confidence": 0.9,
            "reasoning": "Senior engineers always know this"
        }
    }
    ```
    """
    orchestrator = get_provenance_learning_orchestrator()

    try:
        result = await orchestrator.process_training_and_learn(
            feedback_type=feedback_type, feedback_data=feedback_data, source="api"
        )
    except Exception as e:
        logger.error(f"Error processing training feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process feedback")

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/learning/recalibrate")
async def trigger_recalibration(
    holdout_assessment_ids: list[str] = Query(...)
) -> Dict[str, Any]:
    """
    Manually trigger learning recalibration.

    Tests current weights against holdout assessment set.
    Only applies new weights if accuracy improves >1%.

    Query parameters:
    - holdout_assessment_ids: Assessment IDs to use for validation

    Returns:
    - accuracy_before/after: Accuracy before and after recalibration
    - improvement: Percentage improvement
    - weights_rolled_back: Whether new weights were rejected
    """
    if not holdout_assessment_ids:
        raise HTTPException(
            status_code=400, detail="At least one holdout assessment ID required"
        )

    orchestrator = get_provenance_learning_orchestrator()

    # Convert IDs to assessment dictionaries for executor
    # In production, would fetch from database
    holdout_assessments = [
        {"assessment_id": aid} for aid in holdout_assessment_ids
    ]

    try:
        # Note: In production, pass actual assessment_executor function
        result = await orchestrator.perform_learning_recalibration(
            assessment_executor=None,  # Would be actual executor
            holdout_assessments=holdout_assessments,
        )
    except Exception as e:
        logger.error(f"Error during recalibration: {e}")
        raise HTTPException(status_code=500, detail="Failed to recalibrate")

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/system-status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get complete system status including Phase A+B+C+D.

    Returns status of:
    - Phase A: Autonomy (file/email ingestion, queue, processor)
    - Phase B: Governance (all 4 gates, thresholds)
    - Phase C: Provenance (provenance records, audit events)
    - Phase D: Learning (weight updates, credentials learned, metrics)
    """
    orchestrator = get_provenance_learning_orchestrator()
    system_state = orchestrator.get_system_state()

    return {
        "phase_c_provenance": system_state.get("provenance", {}),
        "phase_d_learning": system_state.get("learning", {}),
        "status": "operational",
    }
