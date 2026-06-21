"""Modular training-recommendation layer.

Maps a candidate's upskilling gap to concrete learning options across pluggable
providers. Built-in providers are registered here at import time; to add a
partner, implement the TrainingProvider protocol in `providers/<name>.py`,
register it below, and add its config flag.
"""
from __future__ import annotations

from app.services.training.base import CourseMatch, TrainingProvider
from app.services.training.providers.curated import CuratedCatalogProvider
from app.services.training.providers.ntuc_learninghub import NTUCLearningHubProvider
from app.services.training.providers.skillsfuture import SkillsFutureProvider
from app.services.training.registry import (
    enabled_providers,
    enrich_transition_result,
    recommend_for_capabilities,
    register,
)

# --- Register built-in providers (order is non-significant; results are deduped).
register(CuratedCatalogProvider())
register(SkillsFutureProvider())
register(NTUCLearningHubProvider())
# Add new partners here, e.g.:  register(CourseraProvider())

__all__ = [
    "CourseMatch",
    "TrainingProvider",
    "register",
    "enabled_providers",
    "recommend_for_capabilities",
    "enrich_transition_result",
]
