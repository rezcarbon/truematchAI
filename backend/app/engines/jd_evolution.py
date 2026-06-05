"""JD evolution engine (Pillar 3).

Beyond one-shot JD critique, this analyses how a position's requirements have
changed across versions and recommends how the role should evolve next.

Two layers:
1. DETERMINISTIC drift detection (always runs, reproducible/auditable): compares
   ordered JD versions and flags requirement creep, quality trend, and
   capability churn from the parsed requirements — no LLM, no network.
2. LLM recommendations + an evolved-requirements DRAFT (when a key is configured);
   mock fixture otherwise.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.engines.client import call_claude_json, is_live
from app.engines.prompts import get_prompt

METHOD = "jd-evolution-v1"
_YEARS_RE = re.compile(r"(\d+)\s*\+?\s*(?:years|yrs|yr)", re.I)


def _max_years(text: str | None) -> int | None:
    if not text:
        return None
    nums = [int(m) for m in _YEARS_RE.findall(text)]
    return max(nums) if nums else None


def detect_drift(versions: list[dict]) -> dict[str, Any]:
    """Deterministic longitudinal drift signals across ordered JD versions."""
    signals: list[dict] = []
    if len(versions) < 2:
        return {"method": METHOD, "deterministic": True, "trend": "stable", "drift_signals": []}

    first, last = versions[0], versions[-1]

    # Years-of-experience creep (a classic exclusionary drift).
    y0, y1 = _max_years(first.get("description")), _max_years(last.get("description"))
    if y0 is not None and y1 is not None and y1 > y0:
        signals.append({
            "type": "experience_creep",
            "detail": f"Required experience rose from {y0}+ to {y1}+ years across versions.",
            "direction": "up",
        })

    # Requirement-count growth (scope expansion).
    def _req_count(v: dict) -> int:
        r = v.get("parsed_requirements") or {}
        return len(r.get("required_capabilities") or [])

    c0, c1 = _req_count(first), _req_count(last)
    if c1 > c0:
        signals.append({
            "type": "scope_expansion",
            "detail": f"Required-capability count grew from {c0} to {c1}.",
            "direction": "up",
        })

    # Quality-score trend.
    q0, q1 = first.get("jd_quality_score"), last.get("jd_quality_score")
    trend = "stable"
    if isinstance(q0, int) and isinstance(q1, int):
        if q1 > q0 + 5:
            trend = "improving"
        elif q1 < q0 - 5:
            trend = "degrading"
            signals.append({
                "type": "quality_decline",
                "detail": f"JD quality score fell from {q0} to {q1}.",
                "direction": "down",
            })
    return {"method": METHOD, "deterministic": True, "trend": trend, "drift_signals": signals}


def analyze_evolution(versions: list[dict]) -> dict[str, Any]:
    """Full evolution analysis: deterministic drift + (live) recommendations/draft."""
    drift = detect_drift(versions)
    if len(versions) < 2:
        result = {
            **drift,
            "recommendations": ["Only one JD version on record — no evolution history yet."],
            "evolved_requirements_draft": None,
        }
        return result

    if not is_live():
        return {
            **drift,
            "recommendations": [
                "MOCK: relax the steepest experience requirement to widen the pool.",
                "MOCK: convert credential gates to capability evidence.",
            ],
            "evolved_requirements_draft": "MOCK evolved requirements draft.",
        }

    prompt = get_prompt("jd_evolution")
    history = [
        {
            "version": v.get("version"),
            "quality_score": v.get("jd_quality_score"),
            "required_capabilities": (v.get("parsed_requirements") or {}).get("required_capabilities"),
            "description": v.get("description"),
        }
        for v in versions
    ]
    data = call_claude_json(
        system=prompt.system,
        user_content=prompt.render_user(history=json.dumps(history)),
        max_tokens=2500,
    )
    # Merge deterministic drift signals with the model's analysis (deterministic
    # signals are authoritative and always present for audit).
    data["drift_signals"] = drift["drift_signals"] + (data.get("drift_signals") or [])
    data.setdefault("trend", drift["trend"])
    data["method"] = METHOD
    return data
