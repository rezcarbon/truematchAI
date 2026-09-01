"""Governance engine: coherence, consistency, fidelity, and bias checks.

IP-SAFETY:
  * This module produces raw measures from the model and then evaluates them
    against named gates via core.governance. Threshold VALUES are never present
    here — they live only in the external config and are applied through the
    GovernanceConfig boolean helpers.
  * Client-facing outputs include only pass/fail booleans and qualitative notes.

Each check obtains a raw measure from the model (live when a key is configured,
otherwise a deterministic mock) and evaluates it against the named gate via
core.governance. Threshold VALUES are never present here, and raw measures are
NOT returned to clients — only the pass/fail boolean and qualitative notes.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.core.governance import (
    COHERENCE_THRESHOLD,
    CONSISTENCY_BOUND,
    FIDELITY_THRESHOLD,
    GovernanceConfig,
)
from app.engines.client import call_claude_json, is_live
from app.engines.prompts import get_prompt

logger = logging.getLogger("truematch.governance_engine")


def _measure(value: Any, lo: float, hi: float, default: float) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return default


def check_coherence(assessment: dict, config: GovernanceConfig) -> dict[str, Any]:
    prompt = get_prompt("gov_coherence")
    user = prompt.render_user(assessment=json.dumps(assessment))
    if is_live():
        raw = call_claude_json(system=prompt.system, user_content=user, max_tokens=800)
        measure = _measure(raw.get("measure"), 0.0, 1.0, 0.0)
        note = raw.get("observations", "")
    else:
        measure = 0.88
        note = "MOCK: components and narrative are mutually supportive."
    # IP-SAFETY: `measure` is intentionally NOT included in the returned dict.
    return {
        "gate": COHERENCE_THRESHOLD,
        "passed": config.passes_coherence(measure),
        "observations": note,
    }


def check_consistency(assessment: dict, config: GovernanceConfig) -> dict[str, Any]:
    prompt = get_prompt("gov_consistency")
    user = prompt.render_user(assessment=json.dumps(assessment))
    if is_live():
        raw = call_claude_json(system=prompt.system, user_content=user, max_tokens=800)
        deviation = _measure(raw.get("deviation"), -1.0, 1.0, 1.0)
        note = raw.get("observations", "")
    else:
        deviation = 0.05
        note = "MOCK: conclusion aligns with cited evidence."
    return {
        "gate": CONSISTENCY_BOUND,
        "passed": config.passes_consistency(deviation),
        "observations": note,
    }


def check_fidelity(
    parsed_resume: dict, assessment: dict, config: GovernanceConfig
) -> dict[str, Any]:
    prompt = get_prompt("gov_fidelity")
    user = prompt.render_user(
        parsed_resume=json.dumps(parsed_resume),
        assessment=json.dumps(assessment),
    )
    if is_live():
        raw = call_claude_json(system=prompt.system, user_content=user, max_tokens=1200)
        measure = _measure(raw.get("measure"), 0.0, 1.0, 0.0)
        unsupported = raw.get("unsupported_claims", [])
        note = raw.get("observations", "")
    else:
        measure = 0.93
        unsupported = []
        note = "MOCK: all claims grounded in source."
    return {
        "gate": FIDELITY_THRESHOLD,
        "passed": config.passes_fidelity(measure),
        "unsupported_claims": unsupported,
        "observations": note,
    }


def check_bias(parsed_resume: dict, assessment: dict) -> dict[str, Any]:
    """Bias scan is qualitative — flags only, no numeric threshold involved."""
    prompt = get_prompt("gov_bias")
    user = prompt.render_user(
        parsed_resume=json.dumps(parsed_resume),
        assessment=json.dumps(assessment),
    )
    if is_live():
        raw = call_claude_json(system=prompt.system, user_content=user, max_tokens=1200)
        return {
            "flags": raw.get("flags", []),
            "observations": raw.get("observations", ""),
        }
    return {"flags": [], "observations": "MOCK: no bias signals detected."}
