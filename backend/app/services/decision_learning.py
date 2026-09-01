"""Closes the learning loop: recruiter decisions → learned state → scoring.

Previously feedback was collected but never consumed. This module wires the two
ends together, deterministically (no LLM dependency):

1. `bridge_decision_to_feedback` — every recorded Decision becomes a
   TrainingFeedback signal (the collection side).
2. `reinforce_from_decision` — a positive decision (hire/advance/interview)
   updates a SuccessPattern for that position with the capabilities the hired
   candidate demonstrated (the processing side).
3. `fetch_learned_context_sync` — the assessment pipeline reads that learned
   SuccessPattern back and injects it into the capability prompt (the
   consumption side).

Everything is best-effort and graceful: if there's no learned state yet, the
read returns "" and scoring is unchanged, so this can never break an assessment.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.decision import Decision, DecisionOutcome
from app.models.assessment import Assessment
from app.models.position import Position
from app.models.training import SuccessPattern, TrainingFeedback

logger = logging.getLogger("truematch.decision_learning")

_POSITIVE = {DecisionOutcome.hire, DecisionOutcome.advance, DecisionOutcome.interview}

_FEEDBACK_TYPE = {
    DecisionOutcome.hire: "hire",
    DecisionOutcome.reject: "reject",
    DecisionOutcome.advance: "interested",
    DecisionOutcome.interview: "interested",
    DecisionOutcome.hold: "applied",
}

# Capability components scoring at/above this are treated as "demonstrated".
_DEMONSTRATED_THRESHOLD = 70


def _demonstrated_capabilities(assessment: Assessment) -> list[str]:
    """Capability component names the candidate scored well on."""
    comps = assessment.capability_components or {}
    if not isinstance(comps, dict):
        return []
    out: list[str] = []
    for name, comp in comps.items():
        score = comp.get("score") if isinstance(comp, dict) else comp
        if isinstance(score, (int, float)) and score >= _DEMONSTRATED_THRESHOLD:
            out.append(str(name))
    return out


async def bridge_decision_to_feedback(db, decision: Decision, assessment: Assessment) -> None:
    """Create a TrainingFeedback signal from a recorded decision (async session)."""
    try:
        db.add(
            TrainingFeedback(
                user_id=decision.recruiter_id,
                job_id=decision.position_id,
                candidate_id=assessment.user_id,
                feedback_type=_FEEDBACK_TYPE.get(decision.decision, "applied"),
                outcome=decision.decision.value,
                comments=decision.override_reasoning,
                source="web",
                is_training=True,
            )
        )
    except Exception as exc:  # noqa: BLE001 — learning must never block a decision
        logger.warning("bridge_decision_to_feedback failed: %s", exc)


async def reinforce_from_decision(db, decision: Decision, assessment: Assessment) -> None:
    """Update the position's SuccessPattern from a positive decision (async)."""
    if decision.decision not in _POSITIVE:
        return
    try:
        caps = _demonstrated_capabilities(assessment)
        position = await db.get(Position, decision.position_id)
        category = (position.title or "")[:100] if position else None

        sp = (
            await db.execute(
                select(SuccessPattern).where(SuccessPattern.job_id == decision.position_id)
            )
        ).scalar_one_or_none()
        if sp is None:
            sp = SuccessPattern(
                job_id=decision.position_id,
                job_category=category,
                key_capabilities=[],
                sample_size=0,
                success_rate=0.0,
            )
            db.add(sp)

        merged = sorted({*(sp.key_capabilities or []), *caps})
        sp.key_capabilities = merged
        flag_modified(sp, "key_capabilities")
        sp.sample_size = (sp.sample_size or 0) + 1
        # Confidence grows with sample size, capped.
        sp.confidence_level = min(0.95, 0.5 + 0.05 * sp.sample_size)
        if decision.decision == DecisionOutcome.hire:
            # Track hire rate crudely as positive-confirmation ratio.
            sp.success_rate = min(1.0, (sp.success_rate or 0.0) + 0.1)
        logger.info(
            "Reinforced success pattern",
            extra={
                "position_id": str(decision.position_id),
                "sample_size": sp.sample_size,
                "capabilities": merged[:8],
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("reinforce_from_decision failed: %s", exc)


def fetch_learned_context_sync(db: Session, position_id: uuid.UUID) -> str:
    """Read learned SuccessPattern for a position (sync session, used by the
    assessment worker). Returns a prompt-ready string, or "" if nothing learned.
    """
    try:
        sp = db.execute(
            select(SuccessPattern).where(
                SuccessPattern.job_id == position_id,
                SuccessPattern.is_valid == True,  # noqa: E712
            )
        ).scalar_one_or_none()
        if not sp or not sp.key_capabilities:
            return ""
        caps = ", ".join(list(sp.key_capabilities)[:8])
        return (
            f"LEARNED CONTEXT — across {sp.sample_size} past positive hiring "
            f"decision(s) for this role, successful candidates demonstrated: "
            f"{caps}. Give appropriate weight to these capabilities when the "
            f"resume shows evidence of them (confidence "
            f"{round(sp.confidence_level, 2)})."
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch_learned_context_sync failed: %s", exc)
        return ""
