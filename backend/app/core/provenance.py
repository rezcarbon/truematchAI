"""Assessment provenance for regulatory reproducibility & record-keeping.

Builds a manifest that lets any assessment be reconstructed and independently
audited: hashes of the exact inputs, the model + prompt-registry version used,
the deterministic engine method versions, and whether live or mock reasoning was
in effect. Recorded in the immutable audit trail at pipeline start.

INPUT HASHES (not the raw inputs) are stored, so the audit record proves *which*
inputs were used without itself duplicating candidate PII.
"""
from __future__ import annotations

import hashlib
from typing import Any

from app.config import settings
from app.engines import semantic_match
from app.engines.client import is_live
from app.engines.intake import TRADITIONAL_METHOD
from app.engines.jd_evolution import METHOD as JD_EVOLUTION_METHOD
from app.engines.prompts.registry import PROMPT_REGISTRY_VERSION

PIPELINE_VERSION = "assessment-pipeline-v1"


def _sha256(text: str | None) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def build_manifest(resume_source_text: str | None, jd_text: str | None) -> dict[str, Any]:
    """Provenance manifest recorded at the start of every assessment."""
    return {
        "pipeline_version": PIPELINE_VERSION,
        "prompt_registry_version": PROMPT_REGISTRY_VERSION,
        "reasoning_mode": "live" if is_live() else "mock",
        "model": settings.anthropic_model if is_live() else None,
        "deterministic_engines": {
            "traditional_ats": TRADITIONAL_METHOD,
            "semantic_match": semantic_match.active_method(),
            "jd_evolution": JD_EVOLUTION_METHOD,
        },
        "input_hashes": {
            "resume_sha256": _sha256(resume_source_text),
            "jd_sha256": _sha256(jd_text),
        },
        "enrichment_enabled": settings.enrichment_enabled,
    }
