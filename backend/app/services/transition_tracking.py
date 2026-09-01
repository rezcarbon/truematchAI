"""Phase 3 — longitudinal transition tracking (pure compute + scheduling helpers).

Trajectory and cohort metrics are computed from already-fetched rows so the same
logic serves the async API and the sync Celery worker. No LLM calls here.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from app.config import settings
from app.core.clock import utcnow
from app.models.transition_analysis import (
    OutcomeStatus,
    TransitionAnalysis,
    TransitionOutcome,
    TransitionStatus,
)


def next_review_at(from_time: dt.datetime | None = None) -> dt.datetime:
    base = from_time or utcnow()
    return base + dt.timedelta(days=settings.transition_reassess_interval_days)


def _option_counts(result: dict | None) -> tuple[int, int, int, int, str | None]:
    opts = (result or {}).get("transition_options") or []
    ready = sum(1 for o in opts if o.get("feasibility") == "READY")
    stretch = sum(1 for o in opts if o.get("feasibility") == "STRETCH")
    asp = sum(1 for o in opts if o.get("feasibility") == "ASPIRATIONAL")
    top = opts[0].get("role") if opts else None
    return len(opts), ready, stretch, asp, top


def build_trajectory(analyses: list[TransitionAnalysis]) -> list[dict[str, Any]]:
    """Oldest→newest time-series of completed snapshots for a person/résumé."""
    points: list[dict[str, Any]] = []
    completed = [a for a in analyses if a.status == TransitionStatus.completed]
    for a in sorted(completed, key=lambda x: x.created_at or utcnow()):
        total, ready, stretch, asp, top = _option_counts(a.result)
        points.append({
            "analysis_id": str(a.id),
            "date": a.created_at.isoformat() if a.created_at else None,
            "capability_score": a.capability_score,
            "options": total,
            "ready": ready,
            "stretch": stretch,
            "aspirational": asp,
            "top_role": top,
        })
    return points


def aggregate_metrics(
    analyses: list[TransitionAnalysis], outcomes: list[TransitionOutcome]
) -> dict[str, Any]:
    """Cohort metrics — the 'did people actually move into higher roles?' view."""
    completed = [a for a in analyses if a.status == TransitionStatus.completed]
    readiness = {"ready": 0, "stretch": 0, "aspirational": 0}
    for a in completed:
        _, r, s, asp, _ = _option_counts(a.result)
        readiness["ready"] += r
        readiness["stretch"] += s
        readiness["aspirational"] += asp

    by_status = {st.value: 0 for st in OutcomeStatus}
    for o in outcomes:
        key = o.status.value if hasattr(o.status, "value") else str(o.status)
        by_status[key] = by_status.get(key, 0) + 1

    resolved = by_status.get("achieved", 0) + by_status.get("not_pursued", 0)
    achievement_rate = round(by_status.get("achieved", 0) / resolved, 3) if resolved else None

    return {
        "analyses_total": len(analyses),
        "analyses_completed": len(completed),
        "tracked": sum(1 for a in analyses if a.track),
        "candidates": len({a.user_id for a in analyses}),
        "readiness": readiness,
        "outcomes": by_status,
        "resolved_outcomes": resolved,
        "achievement_rate": achievement_rate,  # achieved / (achieved + not_pursued)
    }
