"""Academic-vs-alternate-experience substitution engine (Pillar 6).

The JD analyzer already names each PROXY requirement and the underlying
capability it stands in for (e.g. "MSc CS" -> "technical depth"). This engine
takes that list and, for each proxy, deliberately searches the candidate's
resume and VERIFIED external evidence for an equivalent of the underlying
capability, then scores the substitution HIGH / MEDIUM / WEAK.

This is the explicit mechanism behind "capability over keywords": it lets the
system say "no MSc, BUT shipped X / published Y = HIGH substitution" rather than
hoping the generic capability pass notices. Output feeds the capability
assessment and the counter-recommendation as an explicit driver.

Returns mock fixtures when no live LLM key is configured (offline/test-safe).
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.engines.client import call_claude_json, is_live
from app.engines.prompts import get_prompt

logger = logging.getLogger("truematch.substitution")

_VALID_STRENGTH = {"HIGH", "MEDIUM", "WEAK"}


def build_substitution_profile(
    proxies: list[dict] | None,
    parsed_resume: dict,
    evidence: list[dict] | None = None,
) -> dict[str, Any]:
    """Score how the candidate's alternate evidence substitutes for each proxy."""
    proxies = proxies or []
    if not proxies:
        return {"substitutions": []}

    if not is_live():
        return _mock(proxies)

    prompt = get_prompt("credential_substitution")
    user = prompt.render_user(
        proxies=json.dumps(proxies),
        parsed_resume=json.dumps(parsed_resume),
        evidence=json.dumps(evidence or []),
    )
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=2500)
    subs = data.get("substitutions") or []
    for s in subs:
        strength = str(s.get("substitution_strength", "")).upper()
        s["substitution_strength"] = strength if strength in _VALID_STRENGTH else "WEAK"
        s.setdefault("alternate_evidence", [])
    return {"substitutions": subs}


def _mock(proxies: list[dict]) -> dict[str, Any]:
    return {
        "_mock": True,
        "substitutions": [
            {
                "requirement": p.get("requirement", "credential"),
                "underlying_capability": p.get("underlying_capability", "capability"),
                "alternate_evidence": ["MOCK: shipped production system relevant to the capability."],
                "substitution_strength": "MEDIUM",
                "rationale": "MOCK substitution rationale.",
            }
            for p in proxies[:3]
        ],
    }
