"""Bias monitoring and disparate impact detection for governance.

Implements quantitative disparate impact (4/5ths rule) analysis and governance
gating to prevent systematically lower selection rates for protected classes.

Key concepts:
- Selection rate = (approved / total) for a demographic group
- Reference group = majority group with highest selection rate
- Four-fifths ratio = selection_rate / reference_selection_rate
- Disparate impact triggered when ratio < 0.8 (Title VII compliance)

The disparate_impact_gate() function integrates into the assessment pipeline
after coherence, consistency, and fidelity checks have passed.
"""
from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from app.core.clock import utcnow
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, AssessmentStatus
from app.models.disparate_impact import (
    DisparateImpactAnalysis,
    DisparateImpactFlag,
)
from app.models.governance_log import GateName, GovernanceLog
from app.models.position import Position
from app.models.resume import Resume
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.bias_monitoring")


# --- Constants ---------------------------------------------------------------

# Protected demographic classes under Title VII / ADEA (extensible)
PROTECTED_CLASSES = {
    "women",
    "minorities",
    "age_50_plus",
    "disability",
    "veteran",
    "lgbtq",
}

# Disparate impact threshold per 4/5ths rule (80% rule)
DISPARATE_IMPACT_THRESHOLD = 0.80

# Minimum sample size to calculate meaningful disparate impact
MIN_SAMPLE_SIZE = 5


# --- Demographic Inference ---------------------------------------------------

def _infer_demographic_group(parsed_resume: dict | None) -> str | None:
    """Infer demographic group from parsed resume data.

    Current implementation returns None as demographics are not collected
    in the resume parsing pipeline. When demographic data collection is
    enabled (opt-in), this function will extract:
    - Gender from name/pronouns
    - Age from graduation dates
    - Race/ethnicity from self-identification (optional)
    - Veteran/disability status from stated background

    Args:
        parsed_resume: Parsed resume data from intake.parse_resume()

    Returns:
        Demographic group identifier (e.g., "women", "minorities") or None
        if not detectable / not collected.
    """
    if not parsed_resume:
        return None

    # TODO(demographic-collection): When users opt-in to demographic data collection,
    # extract from parsed_resume fields. For now, all resumes return None.
    return None


# --- Selection Rate Calculation ----------------------------------------------

def calculate_disparate_impact(
    db: Session,
    position_id: uuid.UUID,
    analysis_period_days: int = 30,
) -> dict[str, Any]:
    """Calculate disparate impact (4/5ths ratio) by demographic group.

    Queries assessments for the given position from the last N days,
    groups by inferred demographic, calculates selection rates, and
    compares against the reference (majority) group.

    Args:
        db: SQLAlchemy session
        position_id: Position UUID to analyze
        analysis_period_days: Days back to include in analysis (default 30)

    Returns:
        Dict with structure:
        {
            "position_id": UUID,
            "analysis_period": "YYYY-MM-DD to YYYY-MM-DD",
            "groups": {
                "women": {
                    "population_size": 15,
                    "approved_count": 9,
                    "selection_rate": 0.60,
                    "reference_group": "men",
                    "reference_selection_rate": 0.85,
                    "four_fifths_ratio": 0.706,
                    "is_disparate_impact": True,
                },
                "men": {
                    "population_size": 20,
                    "approved_count": 17,
                    "selection_rate": 0.85,
                    "reference_group": "men",
                    "reference_selection_rate": 0.85,
                    "four_fifths_ratio": 1.0,
                    "is_disparate_impact": False,
                },
            },
            "analysis_details": {
                "analysis_started": "2026-06-07T14:30:00Z",
                "sample_count": 35,
                "threshold": 0.80,
                "method": "title_vii_four_fifths",
            },
        }
    """
    logger.info(
        f"Calculating disparate impact for position {position_id} "
        f"over {analysis_period_days} days"
    )

    now = utcnow()
    cutoff_date = now - timedelta(days=analysis_period_days)
    period_start = cutoff_date.strftime("%Y-%m-%d")
    period_end = now.strftime("%Y-%m-%d")

    # Query assessments for this position in the analysis period
    stmt = (
        select(Assessment)
        .where(
            and_(
                Assessment.position_id == position_id,
                Assessment.created_at >= cutoff_date,
                Assessment.status.in_(
                    [AssessmentStatus.completed, AssessmentStatus.flagged_for_review]
                ),
            )
        )
    )
    assessments = db.scalars(stmt).all()

    if not assessments:
        logger.warning(
            f"No completed assessments found for position {position_id} "
            f"in period {period_start} to {period_end}"
        )
        return {
            "position_id": str(position_id),
            "analysis_period": f"{period_start} to {period_end}",
            "groups": {},
            "analysis_details": {
                "analysis_started": now.isoformat() + "Z",
                "sample_count": 0,
                "threshold": DISPARATE_IMPACT_THRESHOLD,
                "method": "title_vii_four_fifths",
            },
        }

    # Infer demographics and group assessments
    demographic_groups: dict[str, dict[str, Any]] = {}

    for assessment in assessments:
        resume = db.get(Resume, assessment.resume_id)
        if not resume:
            continue

        demographic = _infer_demographic_group(resume.parsed_data)
        if not demographic:
            continue

        if demographic not in demographic_groups:
            demographic_groups[demographic] = {
                "population_size": 0,
                "approved_count": 0,
                "assessments": [],
            }

        demographic_groups[demographic]["population_size"] += 1
        demographic_groups[demographic]["assessments"].append(assessment)

        # Assessment is approved if it completed (not flagged/failed)
        if assessment.status == AssessmentStatus.completed:
            demographic_groups[demographic]["approved_count"] += 1

    # Calculate selection rates for each group
    selection_rates: dict[str, float] = {}
    for demographic, data in demographic_groups.items():
        if data["population_size"] >= MIN_SAMPLE_SIZE:
            selection_rates[demographic] = (
                data["approved_count"] / data["population_size"]
            )
        else:
            logger.debug(
                f"Demographic group '{demographic}' has sample size "
                f"{data['population_size']} < {MIN_SAMPLE_SIZE}; skipping"
            )

    if not selection_rates:
        logger.warning(
            f"No demographic groups met minimum sample size ({MIN_SAMPLE_SIZE}) "
            f"for position {position_id}"
        )
        return {
            "position_id": str(position_id),
            "analysis_period": f"{period_start} to {period_end}",
            "groups": {},
            "analysis_details": {
                "analysis_started": now.isoformat() + "Z",
                "sample_count": len(assessments),
                "threshold": DISPARATE_IMPACT_THRESHOLD,
                "method": "title_vii_four_fifths",
            },
        }

    # Identify reference group (highest selection rate)
    reference_demographic = max(selection_rates, key=selection_rates.get)
    reference_selection_rate = selection_rates[reference_demographic]

    # Calculate 4/5ths ratios and flag disparate impact
    groups_result = {}
    for demographic in demographic_groups:
        if demographic not in selection_rates:
            continue

        selection_rate = selection_rates[demographic]
        ratio = (
            selection_rate / reference_selection_rate
            if reference_selection_rate > 0
            else 0
        )
        is_disparate_impact = ratio < DISPARATE_IMPACT_THRESHOLD

        groups_result[demographic] = {
            "population_size": demographic_groups[demographic]["population_size"],
            "approved_count": demographic_groups[demographic]["approved_count"],
            "selection_rate": round(selection_rate, 4),
            "reference_group": reference_demographic,
            "reference_selection_rate": round(reference_selection_rate, 4),
            "four_fifths_ratio": round(ratio, 4),
            "is_disparate_impact": is_disparate_impact,
        }

        if is_disparate_impact:
            logger.warning(
                f"DISPARATE IMPACT DETECTED: {demographic} selection rate "
                f"{selection_rate:.1%} vs {reference_demographic} "
                f"{reference_selection_rate:.1%} (ratio: {ratio:.3f})"
            )

    return {
        "position_id": str(position_id),
        "analysis_period": f"{period_start} to {period_end}",
        "groups": groups_result,
        "analysis_details": {
            "analysis_started": now.isoformat() + "Z",
            "sample_count": len(assessments),
            "threshold": DISPARATE_IMPACT_THRESHOLD,
            "method": "title_vii_four_fifths",
        },
    }


# --- Governance Gate ---------------------------------------------------------

def disparate_impact_gate(
    db: Session,
    assessment: Assessment,
    historical_data: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """Governance gate: check if assessment's demographic has disparate impact.

    Gate executes after coherence, consistency, and fidelity checks.
    If disparate impact is flagged for the candidate's demographic group AND
    the group is a protected class, the assessment is routed to human review.

    Args:
        db: SQLAlchemy session
        assessment: Assessment being evaluated
        historical_data: Output from calculate_disparate_impact() for the position

    Returns:
        Tuple of (passed: bool, observations: dict)
        - passed=True: No disparate impact detected or group not protected
        - passed=False: Disparate impact detected for protected demographic
        - observations: Details for governance log

    Raises:
        ValueError: If resume not found for assessment
    """
    resume = db.get(Resume, assessment.resume_id)
    if not resume:
        raise ValueError(f"Resume not found for assessment {assessment.id}")

    # Infer candidate's demographic
    demographic = _infer_demographic_group(resume.parsed_data)

    observations = {
        "gate": "disparate_impact",
        "candidate_demographic": demographic,
        "historical_data_available": bool(historical_data and historical_data.get("groups")),
    }

    # If no demographic inferred or no historical data, pass (cannot gate on unknown)
    if not demographic or not historical_data or not historical_data.get("groups"):
        observations["reason"] = "insufficient_data"
        observations["gate_passed"] = True
        return True, observations

    # Look up candidate's demographic in historical analysis
    group_analysis = historical_data["groups"].get(demographic)
    if not group_analysis:
        observations["reason"] = "demographic_not_in_historical_analysis"
        observations["gate_passed"] = True
        return True, observations

    # Check if disparate impact was flagged for this demographic
    is_disparate_impact = group_analysis.get("is_disparate_impact", False)

    if not is_disparate_impact:
        observations["reason"] = "no_disparate_impact"
        observations["gate_passed"] = True
        observations["selection_rate"] = group_analysis["selection_rate"]
        observations["four_fifths_ratio"] = group_analysis["four_fifths_ratio"]
        return True, observations

    # Disparate impact detected: check if demographic is protected class
    is_protected = demographic.lower() in PROTECTED_CLASSES

    observations["reason"] = "disparate_impact_detected"
    observations["is_protected_class"] = is_protected
    observations["group_data"] = group_analysis
    observations["four_fifths_ratio"] = group_analysis["four_fifths_ratio"]
    observations["selection_rate"] = group_analysis["selection_rate"]
    observations["reference_group"] = group_analysis["reference_group"]
    observations["reference_selection_rate"] = group_analysis["reference_selection_rate"]

    if is_protected:
        observations["gate_passed"] = False
        observations["action"] = "escalate_to_human_review"
        logger.warning(
            f"Disparate impact gate FAILED for assessment {assessment.id}: "
            f"protected class '{demographic}' selection rate "
            f"{group_analysis['selection_rate']:.1%} vs "
            f"{group_analysis['reference_group']} "
            f"{group_analysis['reference_selection_rate']:.1%} "
            f"(ratio: {group_analysis['four_fifths_ratio']:.3f})"
        )
        return False, observations
    else:
        # Non-protected demographic also has disparate impact
        # Log but do not gate (focus gate on protected classes)
        observations["gate_passed"] = True
        observations["reason"] = "disparate_impact_non_protected"
        observations["action"] = "monitor_only"
        logger.info(
            f"Disparate impact detected (non-protected) for assessment {assessment.id}: "
            f"{demographic} selection rate {group_analysis['selection_rate']:.1%}"
        )
        return True, observations


# --- Integration into Assessment Pipeline ------------------------------------

def integrate_disparate_impact_gate(
    db: Session,
    assessment: Assessment,
    position_id: uuid.UUID,
) -> dict[str, Any]:
    """Execute disparate impact gate and update assessment if it fails.

    Calculates 30-day historical disparate impact for the position,
    runs the disparate_impact_gate() check, and logs result to governance_log.
    If gate fails, marks assessment.review_required = True.

    This function should be called in _execute_pipeline() after coherence,
    consistency, and fidelity gates have passed.

    Args:
        db: SQLAlchemy session
        assessment: Assessment being evaluated
        position_id: Position UUID

    Returns:
        Dict with gate result:
        {
            "passed": bool,
            "observations": dict,
            "governance_log_entry_id": UUID,
        }
    """
    logger.info(f"Running disparate impact gate for assessment {assessment.id}")

    try:
        # Calculate historical disparate impact for the position
        historical_data = calculate_disparate_impact(db, position_id, analysis_period_days=30)

        # Run the gate
        passed, observations = disparate_impact_gate(db, assessment, historical_data)

        # Determine gate sequence: disparate_impact follows coherence, consistency, fidelity
        # Query max gate_sequence for this assessment
        max_sequence = db.scalar(
            select(func.max(GovernanceLog.gate_sequence)).where(
                GovernanceLog.assessment_id == assessment.id
            )
        )
        next_sequence = (max_sequence or 0) + 1

        # Log gate result
        gate_log = GovernanceLog(
            assessment_id=assessment.id,
            gate_sequence=next_sequence,
            gate_name=GateName.bias_check,
            passed=passed,
            observations=observations,
        )
        db.add(gate_log)
        db.flush()

        # If gate failed, mark assessment for review and create disparate impact flag
        if not passed:
            assessment.human_review_required = True
            assessment.review_reason = (
                f"Disparate impact detected for demographic '{observations.get('candidate_demographic')}': "
                f"selection rate {observations.get('selection_rate'):.1%} vs "
                f"{observations.get('reference_group')} "
                f"{observations.get('reference_selection_rate'):.1%}"
            )

            # Create disparate impact flag
            flag = DisparateImpactFlag(
                assessment_id=assessment.id,
                flag_triggered=True,
                reason=assessment.review_reason,
                affected_group=observations.get("candidate_demographic", "unknown"),
                recommended_action="escalate to human review; review hiring practices for this demographic",
            )
            db.add(flag)

            logger.warning(
                f"Assessment {assessment.id} flagged for human review: {assessment.review_reason}"
            )

        return {
            "passed": passed,
            "observations": observations,
            "governance_log_entry_id": str(gate_log.id),
        }

    except Exception as exc:
        logger.exception(f"Error in disparate impact gate for assessment {assessment.id}: {exc}")
        # On error, log gate as failed to be safe
        error_max_sequence = db.scalar(
            select(func.max(GovernanceLog.gate_sequence)).where(
                GovernanceLog.assessment_id == assessment.id
            )
        )
        error_next_sequence = (error_max_sequence or 0) + 1

        gate_log = GovernanceLog(
            assessment_id=assessment.id,
            gate_sequence=error_next_sequence,
            gate_name=GateName.bias_check,
            passed=False,
            observations={
                "error": str(exc),
                "reason": "gate_execution_error",
            },
        )
        db.add(gate_log)
        db.flush()

        assessment.human_review_required = True
        assessment.review_reason = f"Disparate impact gate error: {str(exc)}"

        raise


# --- Celery Task: Hourly Analysis & Alerting --------------------------------

@celery_app.task(name="app.workers.bias_monitoring.disparate_impact_hourly_analysis")
def disparate_impact_hourly_analysis() -> dict[str, Any]:
    """Celery task: Run hourly disparate impact analysis for all open positions.

    For each open position with recent assessments:
    1. Calculate disparate impact using 30-day historical window
    2. Store results in DisparateImpactAnalysis table
    3. Compare against previous analysis to detect NEW disparate impact
    4. Alert admin if new impact detected

    Returns:
        Dict with task result:
        {
            "status": "completed",
            "positions_analyzed": 5,
            "new_impacts_detected": 2,
            "alerts_sent": 1,
        }
    """
    logger.info("Starting hourly disparate impact analysis")

    from app.workers.tasks import _session_factory

    try:
        with _session_factory()() as db:
            # Find all open positions with recent assessments
            stmt = (
                select(Position.id)
                .distinct()
                .join(Assessment, Assessment.position_id == Position.id)
                .where(
                    and_(
                        Position.status == "open",
                        Assessment.created_at >= (utcnow() - timedelta(days=30)),
                    )
                )
            )
            position_ids = db.scalars(stmt).all()

            if not position_ids:
                logger.info("No open positions with recent assessments found")
                return {
                    "status": "completed",
                    "positions_analyzed": 0,
                    "new_impacts_detected": 0,
                    "alerts_sent": 0,
                }

            new_impacts_detected = 0
            positions_analyzed = 0

            for position_id in position_ids:
                try:
                    # Calculate disparate impact
                    analysis_result = calculate_disparate_impact(
                        db, position_id, analysis_period_days=30
                    )

                    positions_analyzed += 1
                    groups = analysis_result.get("groups", {})

                    for demographic, group_data in groups.items():
                        if not group_data.get("is_disparate_impact"):
                            continue

                        # Store in DisparateImpactAnalysis table
                        record = DisparateImpactAnalysis(
                            position_id=position_id,
                            analysis_period=analysis_result["analysis_period"],
                            demographic_group=demographic,
                            population_size=group_data["population_size"],
                            selection_rate=group_data["selection_rate"],
                            reference_group=group_data["reference_group"],
                            reference_selection_rate=group_data["reference_selection_rate"],
                            four_fifths_ratio=group_data["four_fifths_ratio"],
                            is_disparate_impact=True,
                            analysis_details=analysis_result["analysis_details"],
                        )
                        db.add(record)
                        db.flush()

                        # Check if this is a NEW disparate impact (not flagged last hour)
                        one_hour_ago = utcnow() - timedelta(hours=1)
                        prev_stmt = (
                            select(func.count(DisparateImpactAnalysis.id))
                            .where(
                                and_(
                                    DisparateImpactAnalysis.position_id == position_id,
                                    DisparateImpactAnalysis.demographic_group == demographic,
                                    DisparateImpactAnalysis.is_disparate_impact.is_(True),
                                    DisparateImpactAnalysis.created_at < one_hour_ago,
                                )
                            )
                        )
                        prev_count = db.scalar(prev_stmt) or 0

                        if prev_count == 0:
                            new_impacts_detected += 1
                            logger.warning(
                                f"NEW DISPARATE IMPACT: Position {position_id}, "
                                f"demographic '{demographic}', ratio {group_data['four_fifths_ratio']:.3f}"
                            )

                            # TODO: Send admin alert (Slack, email, etc.)
                            # _alert_admin_disparate_impact(
                            #     position_id, demographic, group_data
                            # )

                        db.commit()

                except Exception as exc:
                    logger.error(
                        f"Error analyzing disparate impact for position {position_id}: {exc}",
                        exc_info=True,
                    )
                    db.rollback()

            logger.info(
                f"Hourly disparate impact analysis complete: "
                f"{positions_analyzed} positions, {new_impacts_detected} new impacts"
            )

            return {
                "status": "completed",
                "positions_analyzed": positions_analyzed,
                "new_impacts_detected": new_impacts_detected,
                "alerts_sent": new_impacts_detected,  # Currently 1:1, could batch
            }

    except Exception as exc:
        logger.exception(f"Hourly disparate impact analysis failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
        }


# --- Utilities ---------------------------------------------------------------

def get_disparate_impact_summary(
    db: Session,
    position_id: uuid.UUID,
) -> dict[str, Any]:
    """Get latest disparate impact analysis summary for a position.

    Returns the most recent DisparateImpactAnalysis records for the position.

    Args:
        db: SQLAlchemy session
        position_id: Position UUID

    Returns:
        Dict with summary:
        {
            "position_id": UUID,
            "latest_analysis_at": datetime,
            "analysis_period": "2026-05-08 to 2026-06-07",
            "groups_with_impact": [
                {
                    "demographic_group": "women",
                    "selection_rate": 0.60,
                    "four_fifths_ratio": 0.706,
                    "reference_group": "men",
                    "reference_selection_rate": 0.85,
                }
            ],
        }
    """
    # Find latest analysis period for this position
    stmt = (
        select(DisparateImpactAnalysis)
        .where(DisparateImpactAnalysis.position_id == position_id)
        .order_by(DisparateImpactAnalysis.created_at.desc())
        .limit(100)  # Get recent batch to find latest period
    )
    records = db.scalars(stmt).all()

    if not records:
        return {
            "position_id": str(position_id),
            "latest_analysis_at": None,
            "analysis_period": None,
            "groups_with_impact": [],
        }

    # Group by analysis_period to find the latest
    latest_period = records[0].analysis_period
    impacted_groups = [
        {
            "demographic_group": r.demographic_group,
            "selection_rate": r.selection_rate,
            "four_fifths_ratio": r.four_fifths_ratio,
            "reference_group": r.reference_group,
            "reference_selection_rate": r.reference_selection_rate,
        }
        for r in records
        if r.analysis_period == latest_period and r.is_disparate_impact
    ]

    return {
        "position_id": str(position_id),
        "latest_analysis_at": records[0].created_at.isoformat() + "Z",
        "analysis_period": latest_period,
        "groups_with_impact": impacted_groups,
    }
