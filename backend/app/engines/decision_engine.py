"""EU AI Act decision taxonomy engine (Article 14).

This module implements the decision classification and metadata generation
for autonomous, advisory, and escalated decision types per Article 14
of the EU AI Act.

Decision types:
  - approval: Autonomous approval (confidence >= 0.90 + governance passed)
  - advisory: Recommendation requiring human review (confidence 0.40-0.90)
  - escalate: Escalation to human (confidence < 0.40 OR governance failed)

All decisions are marked as "advisory" unless BOTH conditions hold:
  1. confidence/capability_score >= 90 (high confidence)
  2. governance fully passed (all gates: coherence, consistency, fidelity)

Decision metadata includes the rationale and human review requirements
for audit trail and compliance documentation.
"""
from __future__ import annotations

import logging
from typing import NamedTuple

from app.models.assessment import Assessment, DecisionType

logger = logging.getLogger("truematch.decision_engine")


class DecisionMetadata(NamedTuple):
    """Complete decision classification and compliance metadata."""
    decision_type: DecisionType
    requires_human_review: bool
    article_14_compliant: bool
    reasoning: str
    recommendation: str


def determine_decision_type(
    assessment: Assessment,
    capability_score: int,
    governance_passed: bool,
) -> tuple[DecisionType, bool]:
    """Classify an assessment into a decision type per EU AI Act Article 14.

    The decision hierarchy enforces human review unless BOTH conditions are met:
    1. Capability score >= 90 (high confidence in model assessment)
    2. Governance fully passed (all gates: coherence, consistency, fidelity)

    Args:
        assessment: The Assessment model instance
        capability_score: Model confidence score (0-100)
        governance_passed: Boolean indicating if ALL governance gates passed

    Returns:
        tuple[DecisionType, bool]: (decision_type, requires_human_review)

        - approval (False): autonomous approval when high confidence + governance passed
        - advisory (True): recommendation when governance failed OR confidence 40-90
        - escalate (True): escalation when confidence < 40
    """
    # Priority 1: Check if capability score is below escalation threshold
    if capability_score < 40:
        return (DecisionType.escalate, True)

    # Priority 2: Check governance status (mandatory gate)
    if not governance_passed:
        return (DecisionType.advisory, True)

    # Priority 3: Check for high-confidence autonomous approval
    if capability_score >= 90:
        return (DecisionType.approval, False)

    # Priority 4: Default to advisory for mid-range confidence (40-90)
    return (DecisionType.advisory, True)


def generate_decision_metadata(
    assessment: Assessment,
    decision_type: DecisionType,
) -> dict:
    """Generate complete decision metadata for compliance and audit.

    Produces a dict suitable for storage in assessment.review_reason and
    audit trail, with the rationale, recommendation, and compliance status.

    Args:
        assessment: The Assessment model instance
        decision_type: The classified DecisionType

    Returns:
        dict with keys:
            - type (str): decision_type value
            - requires_human_review (bool): Whether human review is needed
            - article_14_compliant (bool): Always True (all paths compliant)
            - reasoning (str): Why this decision type was selected
            - recommendation (str): Next action (e.g., "Review evidence with candidate")
    """
    reasoning = _build_reasoning(assessment, decision_type)
    recommendation = _build_recommendation(assessment, decision_type)

    return {
        "type": decision_type.value,
        "requires_human_review": decision_type != DecisionType.approval,
        "article_14_compliant": True,
        "reasoning": reasoning,
        "recommendation": recommendation,
    }


def _build_reasoning(assessment: Assessment, decision_type: DecisionType) -> str:
    """Construct detailed reasoning for the decision classification."""
    capability = assessment.capability_score or 0
    governance_coherence = assessment.governance_coherence or {}
    governance_consistency = assessment.governance_consistency or {}
    governance_fidelity = assessment.governance_fidelity or {}

    coherence_pass = governance_coherence.get("passed")
    consistency_pass = governance_consistency.get("passed")
    fidelity_pass = governance_fidelity.get("passed")

    if decision_type == DecisionType.approval:
        return (
            f"Autonomous approval granted. Capability assessment demonstrates "
            f"high confidence (score={capability}), and all governance gates passed: "
            f"coherence={coherence_pass}, consistency={consistency_pass}, "
            f"fidelity={fidelity_pass}. Article 14 autonomy threshold met."
        )

    elif decision_type == DecisionType.advisory:
        reasons = []
        if capability < 90:
            reasons.append(f"capability score ({capability}) below autonomy threshold (90)")
        if coherence_pass is False:
            reasons.append("coherence governance gate failed")
        if consistency_pass is False:
            reasons.append("consistency governance gate failed")
        if fidelity_pass is False:
            reasons.append("fidelity governance gate failed")

        reason_str = "; ".join(reasons) if reasons else "governance or confidence constraints"
        return (
            f"Advisory recommendation issued. Decision routed to human review due to: "
            f"{reason_str}. Article 14 requires human oversight for this confidence/governance profile."
        )

    else:  # escalate
        return (
            f"Escalation required. Capability assessment confidence ({capability}) "
            f"is below escalation threshold (40). High-risk decisions require "
            f"human review before any autonomous action. Article 14 escalation protocol triggered."
        )


def _build_recommendation(assessment: Assessment, decision_type: DecisionType) -> str:
    """Construct actionable recommendation based on decision type."""
    if decision_type == DecisionType.approval:
        return (
            "Proceed with autonomous decision. High confidence assessment is approved for "
            "automated processing. Document this approval in audit trail per Article 14."
        )

    elif decision_type == DecisionType.advisory:
        return (
            "Review assessment with candidate and hiring team. Present capability evidence "
            "and governance observations. Human reviewer must validate conclusion before "
            "proceeding. Record human decision and reasoning for compliance audit."
        )

    else:  # escalate
        return (
            "Escalate to senior reviewer or hiring manager. Low-confidence assessment "
            "requires high-level human judgment. Do not proceed with autonomous decision. "
            "Gather additional evidence or request candidate clarification before final determination."
        )


def apply_decision_to_assessment(
    assessment: Assessment,
    decision_type: DecisionType,
    governance_passed: bool,
) -> None:
    """Apply decision classification and metadata directly to Assessment model.

    This convenience function updates all decision-related fields on the
    assessment instance (does NOT commit to DB — caller manages session).

    Args:
        assessment: Assessment instance to update
        decision_type: The classified DecisionType
        governance_passed: Boolean indicating if governance gates passed
    """
    metadata = generate_decision_metadata(assessment, decision_type)

    assessment.decision_type = decision_type
    assessment.human_review_required = metadata["requires_human_review"]
    assessment.article_14_compliant = metadata["article_14_compliant"]
    assessment.review_reason = metadata["reasoning"]

    logger.info(
        "Decision applied to assessment",
        extra={
            "assessment_id": str(assessment.id),
            "decision_type": decision_type.value,
            "requires_human_review": assessment.human_review_required,
            "capability_score": assessment.capability_score,
            "governance_passed": governance_passed,
        },
    )
