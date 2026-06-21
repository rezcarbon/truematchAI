"""Transition Intelligence engine.

A layer ON TOP of the capability verdict: given a candidate's ALREADY-EVIDENCED
capability (score + components) and their parsed résumé, it predicts the
adjacent / higher-complexity roles they could realistically transition into, the
concrete upskilling that closes the gap, and an HONEST timeline.

This is prediction grounded in evidence — the candidate-mobility analogue of the
platform's no-fabrication discipline:
  * Every option is reasoned only from the supplied capability components and
    résumé facts; ungrounded options are dropped, never emitted.
  * Feasibility is tiered (READY / STRETCH / ASPIRATIONAL) so a real gap is named
    as a gap, not hidden.
  * Timelines are month RANGES with an explicit confidence and basis — never
    false precision.
  * No physiological / biometric / wearable signal is used or assumed (none is
    available in the hiring context). No patented method or threshold is encoded
    here; the engine reasons over the existing capability signals via the LLM.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.engines.client import call_claude_json, is_live
from app.engines.prompts import get_prompt

logger = logging.getLogger("truematch.transition_intelligence")

_VALID_STRENGTHS = {"HIGH", "MEDIUM", "WEAK"}
_VALID_FEASIBILITY = {"READY", "STRETCH", "ASPIRATIONAL"}
_VALID_DIRECTION = {"lateral", "upward", "adjacent"}
_VALID_CONFIDENCE = {"low", "medium", "high"}


def assess_transition(
    *,
    parsed_resume: dict,
    capability: dict,
    current_role: str = "",
    target: str = "",
    role_context: str = "",
) -> dict[str, Any]:
    """Return grounded transition options for an evidenced candidate.

    Shape:
        {
          "readiness_summary": str,
          "transition_options": [
            {"role", "direction", "feasibility", "rationale",
             "transferable_strengths": [str],
             "upskilling_gap": [{"capability","why","how"}],
             "timeline": {"months_min","months_max","confidence","basis"},
             "evidence_strength": "HIGH|MEDIUM|WEAK"},
            ...
          ],
          "honesty_notes": str,
          "method": "transition-intelligence-v1",
          "dropped_ungrounded": int,
        }
    """
    if not is_live():
        return _mock_transition(parsed_resume, capability, current_role)

    prompt = get_prompt("transition_intelligence")
    user = prompt.render_user(
        current_role=current_role or "(not specified)",
        capability=json.dumps(capability or {}),
        parsed_resume=json.dumps(parsed_resume or {}),
        target=target or "",
        role_context=role_context or "",
    )
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=4000)
    return _normalize(data)


def _coerce_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple)):
        return " ".join(_coerce_str(i) for i in x if i not in (None, ""))
    if isinstance(x, dict):
        return " ".join(f"{k}: {_coerce_str(v)}" for k, v in x.items())
    return str(x)


def _clamp_months(v: Any, default: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return default
    return max(0, min(120, n))  # 0..10 years; nothing beyond that is a credible plan


def _normalize_timeline(t: Any) -> dict[str, Any]:
    t = t if isinstance(t, dict) else {}
    lo = _clamp_months(t.get("months_min"), 6)
    hi = _clamp_months(t.get("months_max"), max(lo, 12))
    if hi < lo:
        lo, hi = hi, lo
    conf = _coerce_str(t.get("confidence")).lower()
    if conf not in _VALID_CONFIDENCE:
        conf = "low"
    return {"months_min": lo, "months_max": hi, "confidence": conf,
            "basis": _coerce_str(t.get("basis")).strip()}


def _normalize_gap(items: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for g in items if isinstance(items, list) else []:
        if not isinstance(g, dict):
            # tolerate a bare string capability
            cap = _coerce_str(g).strip()
            if cap:
                out.append({"capability": cap, "why": "", "how": ""})
            continue
        cap = _coerce_str(g.get("capability")).strip()
        if not cap:
            continue
        out.append({
            "capability": cap,
            "why": _coerce_str(g.get("why")).strip(),
            "how": _coerce_str(g.get("how")).strip(),
        })
    return out


def _normalize(data: dict) -> dict[str, Any]:
    """Enforce the grounded-prediction contract on the model's output."""
    options: list[dict] = []
    dropped = 0
    for o in data.get("transition_options") or []:
        if not isinstance(o, dict):
            dropped += 1
            continue
        role = _coerce_str(o.get("role")).strip()
        rationale = _coerce_str(o.get("rationale")).strip()
        feasibility = _coerce_str(o.get("feasibility")).upper()
        strength = _coerce_str(o.get("evidence_strength")).upper()
        # An option with no role, no rationale, or an invalid feasibility/strength
        # is ungrounded — drop it rather than present speculation as analysis.
        if not role or not rationale or feasibility not in _VALID_FEASIBILITY \
                or strength not in _VALID_STRENGTHS:
            dropped += 1
            continue
        direction = _coerce_str(o.get("direction")).lower()
        if direction not in _VALID_DIRECTION:
            direction = "adjacent"
        strengths = [_coerce_str(s).strip() for s in (o.get("transferable_strengths") or [])
                     if _coerce_str(s).strip()]
        options.append({
            "role": role,
            "direction": direction,
            "feasibility": feasibility,
            "rationale": rationale,
            "transferable_strengths": strengths,
            "upskilling_gap": _normalize_gap(o.get("upskilling_gap")),
            "timeline": _normalize_timeline(o.get("timeline")),
            "evidence_strength": strength,
        })

    if dropped:
        logger.info("transition_intelligence dropped %d ungrounded option(s)", dropped)

    return {
        "readiness_summary": _coerce_str(data.get("readiness_summary")).strip(),
        "transition_options": options,
        "honesty_notes": _coerce_str(data.get("honesty_notes")).strip(),
        "method": "transition-intelligence-v1",
        "dropped_ungrounded": dropped,
    }


def _mock_transition(parsed_resume: dict, capability: dict, current_role: str) -> dict[str, Any]:
    """Deterministic offline fixture (no Anthropic key). Never used in production."""
    cap = int((capability or {}).get("score") or 0)
    feasibility = "READY" if cap >= 70 else "STRETCH" if cap >= 50 else "ASPIRATIONAL"
    return {
        "readiness_summary": (
            f"Mock readiness view (no live model). Anchored on a capability verdict "
            f"of {cap}. Real transitions are grounded in evidenced components."
        ),
        "transition_options": [
            {
                "role": "Adjacent senior role in the same family",
                "direction": "upward",
                "feasibility": feasibility,
                "rationale": "Mock: derived from the capability components present in the résumé.",
                "transferable_strengths": [str(s) for s in (parsed_resume.get("skills") or [])][:4],
                "upskilling_gap": [
                    {"capability": "Role-specific leadership exposure",
                     "why": "Higher-complexity roles require demonstrated scope.",
                     "how": "Targeted stretch assignment or certification."}
                ],
                "timeline": {"months_min": 6, "months_max": 12, "confidence": "low",
                             "basis": "Mock estimate (offline)."},
                "evidence_strength": "MEDIUM",
            }
        ],
        "honesty_notes": "Mock output; no transition was inferred beyond the résumé evidence.",
        "method": "transition-intelligence-v1",
        "dropped_ungrounded": 0,
    }
