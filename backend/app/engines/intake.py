"""Intake engine: resume parsing, JD analysis, traditional ATS simulation.

Each function renders a server-side prompt and, when a live Anthropic key is
configured (`client.is_live()`), calls Claude and validates the JSON result.
Without a key, deterministic MOCK fixtures are returned so the pipeline remains
runnable offline / in tests. Production MUST configure a real key.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.engines import text_utils
from app.engines.client import call_claude_json, is_live
from app.engines.prompts import get_prompt

logger = logging.getLogger("truematch.intake")


def _clamp_score(value: Any, default: int = 0) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return default


def parse_resume(resume_text: str, supplementary: dict | None = None) -> dict[str, Any]:
    """Parse a resume into structured data + a faithful narrative summary."""
    prompt = get_prompt("resume_parse")
    user = prompt.render_user(
        resume_text=resume_text or "",
        supplementary=json.dumps(supplementary or {}),
    )
    if not is_live():
        return _mock_parsed_resume()
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=3000)
    data.setdefault("skills", [])
    data.setdefault("experience", [])
    data.setdefault("narrative", data.get("summary", ""))
    return data


def analyze_jd(jd_text: str) -> dict[str, Any]:
    """Decompose a job description into structured requirements."""
    prompt = get_prompt("jd_analyze")
    user = prompt.render_user(jd_text=jd_text or "")
    if not is_live():
        return _mock_requirements()
    data = call_claude_json(system=prompt.system, user_content=user, max_tokens=2000)
    data.setdefault("required_capabilities", [])
    data.setdefault("preferred_capabilities", [])
    return data


TRADITIONAL_METHOD = "keyword-tfidf-v1"


def traditional_ats(
    jd_text: str, resume_text: str, idf: dict[str, float] | None = None
) -> dict[str, Any]:
    """DETERMINISTIC keyword/heuristic ATS baseline (no LLM).

    TF(-IDF) weighted overlap between the JD's salient terms (unigrams + bigrams)
    and the candidate's resume text. When an `idf` map from the accumulating JD
    corpus is supplied, role-distinctive terms count more than terms common to
    every posting (the system learns as it sees more JDs); otherwise plain term
    frequency is used. Reproducible and role-differentiated; blind to inferred
    capability — the gap to the capability score is the signal.
    """
    jd_tf = text_utils.term_frequencies(jd_text)
    resume_terms = set(text_utils.term_frequencies(resume_text).keys())
    if not jd_tf:
        return {"score": 0, "method": TRADITIONAL_METHOD, "deterministic": True,
                "idf_weighted": bool(idf), "matched_keywords": [], "missing_keywords": []}

    weights = {t: tf * (idf.get(t, 1.0) if idf else 1.0) for t, tf in jd_tf.items()}
    total_weight = sum(weights.values())
    matched_weight = sum(w for t, w in weights.items() if t in resume_terms)
    score = round(100 * matched_weight / total_weight) if total_weight else 0

    by_weight = sorted(jd_tf, key=lambda t: weights[t], reverse=True)
    return {
        "score": score,
        "method": TRADITIONAL_METHOD,
        "deterministic": True,
        "idf_weighted": bool(idf),
        "matched_keywords": [t for t in by_weight if t in resume_terms][:15],
        "missing_keywords": [t for t in by_weight if t not in resume_terms][:15],
    }


# --- Mock fixtures (clearly marked) -----------------------------------------

def _mock_parsed_resume() -> dict[str, Any]:
    return {
        "_mock": True,
        "contact": {"name": "Candidate"},
        "summary": "MOCK parsed summary.",
        "experience": [
            {
                "title": "Senior Engineer",
                "org": "Acme",
                "start": "2019",
                "end": "2024",
                "highlights": ["Led platform migration", "Mentored 4 engineers"],
            }
        ],
        "education": [],
        "skills": ["python", "distributed systems"],
        "certifications": [],
    }


def _mock_requirements() -> dict[str, Any]:
    return {
        "_mock": True,
        "responsibilities": ["Design backend services"],
        "required_capabilities": ["backend engineering", "systems design"],
        "preferred_capabilities": ["cloud infra"],
        "seniority": "senior",
        "domain": "software",
        "hard_constraints": [],
    }


def _mock_traditional() -> dict[str, Any]:
    return {
        "_mock": True,
        "score": 62,
        "matched_keywords": ["python"],
        "missing_keywords": ["kubernetes"],
        "rationale": "MOCK: keyword-overlap baseline.",
    }
