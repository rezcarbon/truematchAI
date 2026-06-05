"""Shared test configuration.

Force deterministic mock fixtures for all engine tests (no network), and ensure
governance env overrides from the host shell do not leak into tests.
"""
from __future__ import annotations

import os

# Must be set before app.config is imported anywhere.
os.environ.setdefault("LLM_FORCE_MOCK", "true")
# Tests use the deterministic lexical matcher (no model download / network).
os.environ.setdefault("SEMANTIC_USE_EMBEDDINGS", "false")
for _k in (
    "GOVERNANCE_COHERENCE_THRESHOLD",
    "GOVERNANCE_CONSISTENCY_BOUND",
    "GOVERNANCE_FIDELITY_THRESHOLD",
    "GOVERNANCE_COUNTER_REC_DELTA",
):
    os.environ.pop(_k, None)
