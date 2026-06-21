"""Interview-content analysis.

Turn an interview transcript into a structured, role-aware scorecard: per-
competency ratings, evidence-cited strengths/concerns, red-flag detection, and
an overall recommendation. Deterministic mock fallback when no LLM key is set
(so the pipeline is exercisable offline), real Claude reasoning when live.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.engines.client import call_claude_json, is_live, select_model

logger = logging.getLogger("truematch.interview_analysis")

_RECS = {"strong_yes", "yes", "no", "strong_no"}

_SYSTEM = (
    "You are an impartial interview assessor. Given an interview transcript and "
    "the role's requirements, score the candidate ONLY on evidence present in "
    "the transcript. Never invent answers the candidate did not give. Rate each "
    "relevant competency 1-5 (5=excellent). Cite a brief quote/paraphrase for "
    "each strength and concern. Flag evasiveness, contradictions, or unverified "
    "claims as red flags. Return a single overall recommendation."
)


def _competencies_from_requirements(requirements: dict | None) -> list[str]:
    req = requirements or {}
    caps = req.get("required_capabilities") or req.get("capabilities") or []
    out = [str(c).strip() for c in caps if str(c).strip()]
    return out[:8] or ["communication", "role_knowledge", "problem_solving"]


def _mock_analysis(competencies: list[str], transcript: str) -> dict[str, Any]:
    # Deterministic: score scales with how much the transcript references each
    # competency token — reproducible, no LLM, useful for offline tests/demos.
    low = transcript.lower()
    scores = {}
    for c in competencies:
        hits = sum(1 for tok in c.lower().split() if tok in low)
        scores[c] = max(1, min(5, 2 + hits))
    avg = sum(scores.values()) / max(len(scores), 1)
    rec = "yes" if avg >= 3 else "no"
    return {
        "competency_scores": scores,
        "strengths": ["(mock) Referenced relevant experience in the transcript."],
        "concerns": ["(mock) Limited depth on some required areas."],
        "red_flags": [],
        "overall_recommendation": rec,
        "summary": "Mock analysis (no LLM configured): scored deterministically "
        "from transcript keyword coverage.",
        "method": "mock",
    }


def analyze_interview(
    transcript: str,
    requirements: dict | None,
    context: dict | None = None,
) -> dict[str, Any]:
    """Analyze an interview transcript into a structured scorecard dict."""
    competencies = _competencies_from_requirements(requirements)
    if not transcript or not transcript.strip():
        return {
            "competency_scores": {},
            "strengths": [],
            "concerns": [],
            "red_flags": ["Empty transcript — nothing to assess."],
            "overall_recommendation": "no",
            "summary": "No transcript content was provided.",
            "method": "empty",
        }

    if not is_live():
        return _mock_analysis(competencies, transcript)

    user = (
        f"ROLE REQUIREMENTS:\n{json.dumps(requirements or {})}\n\n"
        f"COMPETENCIES TO SCORE (1-5 each): {', '.join(competencies)}\n\n"
        f"INTERVIEW CONTEXT:\n{json.dumps(context or {})}\n\n"
        f"TRANSCRIPT:\n{transcript[:20000]}\n\n"
        "Return JSON: {competency_scores:{name:int}, strengths:[str], "
        "concerns:[str], red_flags:[str], overall_recommendation:"
        "'strong_yes'|'yes'|'no'|'strong_no', summary:str}"
    )
    try:
        data = call_claude_json(
            system=_SYSTEM,
            user_content=user,
            max_tokens=2000,
            model=select_model("secondary"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Interview analysis LLM call failed: %s", exc)
        return _mock_analysis(competencies, transcript)

    # Normalize/clamp.
    scores = {}
    for k, v in (data.get("competency_scores") or {}).items():
        try:
            scores[str(k)] = max(1, min(5, int(round(float(v)))))
        except (TypeError, ValueError):
            continue
    rec = str(data.get("overall_recommendation") or "").lower()
    if rec not in _RECS:
        avg = sum(scores.values()) / max(len(scores), 1)
        rec = "yes" if avg >= 3 else "no"
    return {
        "competency_scores": scores,
        "strengths": [str(s) for s in (data.get("strengths") or [])][:10],
        "concerns": [str(s) for s in (data.get("concerns") or [])][:10],
        "red_flags": [str(s) for s in (data.get("red_flags") or [])][:10],
        "overall_recommendation": rec,
        "summary": str(data.get("summary") or ""),
        "method": "llm",
    }
