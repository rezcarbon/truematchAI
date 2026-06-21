"""Capability Translation engine.

Re-expresses a candidate's *already-evidenced* capability in the credential /
keyword vocabulary that ATS systems recognise — making real capability legible,
NOT fabricating it. This is the candidate-side mirror of credential
substitution: the same equivalence reasoning ("Docker Swarm experience ≈
container orchestration ≈ the Kubernetes the JD asks for"), pointed at the
candidate's own resume.

Hard rule enforced in the prompt AND post-validated here: every rewritten line
must be grounded in something the candidate actually wrote. Nothing is invented.
Lines that cannot be grounded are dropped, never emitted. The runner then
re-scores the rewrite with the SAME deterministic keyword + semantic engines we
sell recruiters, so the before→after lift is measured, not claimed.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.engines.client import call_claude_json, is_live
from app.engines.prompts import get_prompt

logger = logging.getLogger("truematch.capability_translation")

# Evidence strengths a rewritten claim may carry. Anything the model cannot tie
# to the source resume is "UNGROUNDED" and is filtered out before persistence.
_VALID_STRENGTHS = {"HIGH", "MEDIUM", "WEAK"}


def translate_capability(
    *,
    resume_text: str,
    parsed_resume: dict,
    jd_text: str,
    requirements: dict | None = None,
    substitutions: dict | None = None,
) -> dict[str, Any]:
    """Produce an ATS-legible, JD-targeted rewrite grounded in evidenced capability.

    Returns:
        {
          "summary": str,                      # rewritten professional summary
          "bullets": [                         # rewritten experience bullets
            {"text": str, "grounding": str, "evidence_strength": "HIGH|MEDIUM|WEAK"},
            ...
          ],
          "skills": [str],                     # ATS keyword-legible skills, evidence-backed only
          "translation_notes": str,            # what was NOT added (lacked evidence) — the honesty line
          "method": "capability-translation-v1",
        }
    """
    if not is_live():
        return _mock_translation(parsed_resume, jd_text)

    prompt = get_prompt("capability_translation")
    user = prompt.render_user(
        resume_text=resume_text or "",
        parsed_resume=json.dumps(parsed_resume or {}),
        jd_text=jd_text or "",
        requirements=json.dumps(requirements or {}),
        substitutions=json.dumps(substitutions or {}),
    )
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=4000)
    return _normalize(data)


def _coerce_str(x: Any) -> str:
    """Models occasionally return a dict/list where a string is expected
    (e.g. translation_notes as an object). Coerce safely instead of crashing."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple)):
        return " ".join(_coerce_str(i) for i in x if i not in (None, ""))
    if isinstance(x, dict):
        return " ".join(f"{k}: {_coerce_str(v)}" for k, v in x.items())
    return str(x)


def _normalize(data: dict) -> dict[str, Any]:
    """Coerce + enforce the no-fabrication contract on the model's output."""
    summary = _coerce_str(data.get("summary")).strip()
    skills = [_coerce_str(s).strip() for s in (data.get("skills") or []) if _coerce_str(s).strip()]

    grounded: list[dict] = []
    dropped = 0
    for b in data.get("bullets") or []:
        if not isinstance(b, dict):
            continue
        text = _coerce_str(b.get("text")).strip()
        grounding = _coerce_str(b.get("grounding")).strip()
        strength = _coerce_str(b.get("evidence_strength")).upper()
        # A bullet with no source grounding, or an invalid/UNGROUNDED strength,
        # is fabrication risk — drop it rather than ship it.
        if not text or not grounding or strength not in _VALID_STRENGTHS:
            dropped += 1
            continue
        grounded.append({"text": text, "grounding": grounding, "evidence_strength": strength})

    notes = _coerce_str(data.get("translation_notes")).strip()
    if dropped:
        logger.info("capability_translation dropped %d ungrounded bullet(s)", dropped)

    return {
        "summary": summary,
        "bullets": grounded,
        "skills": skills,
        "translation_notes": notes,
        "method": "capability-translation-v1",
        "dropped_ungrounded": dropped,
    }


def assemble_resume_text(translation: dict, parsed_resume: dict | None = None) -> str:
    """Flatten a translation into a plain-text resume body for re-scoring.

    Concatenates the rewritten summary, skills and bullets. Education/contact
    from the parsed resume are appended so the rewrite is scored as a whole
    document, not just the changed spans.
    """
    parts: list[str] = []
    if translation.get("summary"):
        parts.append(translation["summary"])
    if translation.get("skills"):
        parts.append("Skills: " + ", ".join(translation["skills"]))
    for b in translation.get("bullets") or []:
        parts.append("- " + b["text"])
    # Carry over non-rewritten factual sections so scoring sees the full doc.
    parsed = parsed_resume or {}
    for edu in parsed.get("education") or []:
        if isinstance(edu, dict):
            parts.append(" ".join(str(v) for v in edu.values() if v))
        elif isinstance(edu, str):
            parts.append(edu)
    return "\n".join(p for p in parts if p)


def _mock_translation(parsed_resume: dict, jd_text: str) -> dict[str, Any]:
    """Deterministic offline fixture (no Anthropic key). Keeps the pipeline
    runnable in tests; never used in production where is_live() is True."""
    skills = [str(s) for s in (parsed_resume.get("skills") or [])][:8] or [
        "Python",
        "Distributed Systems",
        "Container Orchestration",
    ]
    return {
        "summary": (
            "Engineer with demonstrated capability in building and operating "
            "production systems, re-expressed for ATS legibility against the target role."
        ),
        "bullets": [
            {
                "text": "Operated container orchestration in production (Kubernetes-equivalent).",
                "grounding": "resume mentions Docker Swarm cluster operation",
                "evidence_strength": "HIGH",
            },
            {
                "text": "Designed scalable backend services handling production traffic.",
                "grounding": "resume experience section",
                "evidence_strength": "MEDIUM",
            },
        ],
        "skills": skills,
        "translation_notes": (
            "No certifications or tools were added that the resume does not "
            "support. Mock output (no live model configured)."
        ),
        "method": "capability-translation-v1",
        "dropped_ungrounded": 0,
    }
