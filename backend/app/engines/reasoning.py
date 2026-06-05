"""Reasoning engine: capability assessment, trajectory, JD interrogation,
counter-recommendation.

Each function calls Claude when a live key is configured (`client.is_live()`)
and validates the JSON result; otherwise it returns deterministic MOCK fixtures
so the pipeline runs offline / in tests.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.engines.client import call_claude_json, is_live
from app.engines.prompts import get_prompt

logger = logging.getLogger("truematch.reasoning")


def _clamp_score(value: Any, default: int = 0) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return default


def assess_capability(
    requirements: dict,
    parsed_resume: dict,
    raw_narrative: str | None,
    evidence: list[dict] | None = None,
    substitutions: dict | None = None,
) -> dict[str, Any]:
    prompt = get_prompt("capability_assess")
    user = prompt.render_user(
        requirements=json.dumps(requirements),
        parsed_resume=json.dumps(parsed_resume),
        raw_narrative=raw_narrative or "",
    )
    # Feed verified external evidence + credential substitutions as additional
    # grounding so capability reasoning can credit alternate-to-academic proof.
    if evidence:
        user += "\n\nVERIFIED EXTERNAL EVIDENCE (status-tagged):\n" + json.dumps(evidence)
    if substitutions and substitutions.get("substitutions"):
        user += "\n\nCREDENTIAL SUBSTITUTIONS:\n" + json.dumps(substitutions["substitutions"])
    if not is_live():
        return _mock_capability()
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=3000)
    data["score"] = _clamp_score(data.get("score"))
    components = data.get("components") or {}
    for comp in components.values():
        if isinstance(comp, dict):
            comp["score"] = _clamp_score(comp.get("score"))
    data["components"] = components
    data.setdefault("narrative", "")
    return data


def analyze_trajectory(parsed_resume: dict) -> dict[str, Any]:
    prompt = get_prompt("trajectory")
    user = prompt.render_user(parsed_resume=json.dumps(parsed_resume))
    if not is_live():
        return _mock_trajectory()
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=2500)
    data.setdefault("trajectory", {})
    data.setdefault("narrative", "")
    return data


def interrogate_jd(jd_text: str) -> dict[str, Any]:
    prompt = get_prompt("jd_interrogation")
    user = prompt.render_user(jd_text=jd_text or "")
    if not is_live():
        return _mock_jd_review()
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=1500)
    data["quality_score"] = _clamp_score(data.get("quality_score"))
    data.setdefault("issues", [])
    return data


def counter_recommendation(
    traditional: dict,
    capability: dict,
    requirements: dict,
    substitutions: dict | None = None,
) -> dict[str, Any]:
    prompt = get_prompt("counter_recommendation")
    user = prompt.render_user(
        traditional=json.dumps(traditional),
        capability=json.dumps(capability),
        requirements=json.dumps(requirements),
    )
    # Credential substitutions are an explicit driver of the counter-rec: they
    # justify advancing a candidate who lacks the literal credential.
    if substitutions and substitutions.get("substitutions"):
        user += "\n\nCREDENTIAL SUBSTITUTIONS (alternate evidence vs proxy requirements):\n" + json.dumps(
            substitutions["substitutions"]
        )
    if not is_live():
        return _mock_counter()
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=2500)
    data.setdefault("reasoning", "")
    data.setdefault("evidence", [])
    return data


# --- Mock fixtures (clearly marked) -----------------------------------------

def _mock_capability() -> dict[str, Any]:
    return {
        "_mock": True,
        "score": 81,
        "components": {
            "domain_depth": {"score": 84, "evidence": "MOCK: platform migration leadership."},
            "problem_solving": {"score": 80, "evidence": "MOCK: cross-team debugging record."},
            "collaboration": {"score": 78, "evidence": "MOCK: mentored 4 engineers."},
        },
        "narrative": "MOCK capability narrative: candidate demonstrates strong delivery.",
    }


def _mock_trajectory() -> dict[str, Any]:
    return {
        "_mock": True,
        "trajectory": {
            "direction": "ascending",
            "velocity": "steady",
            "inflection_points": ["promotion to senior in 2021"],
        },
        "narrative": "MOCK trajectory narrative: consistent scope expansion.",
    }


def _mock_jd_review() -> dict[str, Any]:
    return {
        "_mock": True,
        "quality_score": 71,
        "issues": [
            {"type": "vague_requirement", "severity": "medium", "detail": "MOCK: '5+ years' unscoped."}
        ],
    }


def _mock_counter() -> dict[str, Any]:
    return {
        "_mock": True,
        "reasoning": "MOCK: keyword baseline penalized non-matching titles despite strong evidence.",
        "evidence": [
            {"claim": "Led platform migration", "support": "Demonstrates systems-design capability."}
        ],
    }
