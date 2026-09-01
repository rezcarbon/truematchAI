"""Training-provider registry.

Aggregates learning recommendations across all ENABLED providers, dedups, and
enriches a Transition Intelligence result in place. Providers register
themselves at import time (see `__init__.py`); adding a partner never touches
this file.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import settings
from app.services.training.base import CourseMatch, TrainingProvider

logger = logging.getLogger("truematch.training")

_PROVIDERS: list[TrainingProvider] = []


def register(provider: TrainingProvider) -> None:
    """Register a provider once (idempotent by provider name)."""
    if any(p.name == provider.name for p in _PROVIDERS):
        return
    _PROVIDERS.append(provider)


def enabled_providers() -> list[TrainingProvider]:
    out = []
    for p in _PROVIDERS:
        try:
            if p.enabled():
                out.append(p)
        except Exception as exc:  # noqa: BLE001
            logger.warning("training provider %s enabled() failed: %s", getattr(p, "name", "?"), exc)
    return out


def recommend_for_capabilities(
    capabilities: list[str], context: dict[str, Any] | None = None, per_capability_cap: int = 3
) -> list[CourseMatch]:
    """Collect course matches across enabled providers, deduped, capped per capability."""
    if not getattr(settings, "training_recommendations_enabled", True):
        return []
    caps = [c for c in (capabilities or []) if c and c.strip()]
    if not caps:
        return []
    ctx = context or {}
    matches: list[CourseMatch] = []
    seen: set[tuple[str, str, str]] = set()
    for p in enabled_providers():
        try:
            for m in p.match(caps, ctx):
                key = (m.capability.lower(), m.title.lower(), m.provider.lower())
                if key in seen:
                    continue
                seen.add(key)
                matches.append(m)
        except Exception as exc:  # noqa: BLE001 — one provider must not fail the batch
            logger.warning("training provider %s match() failed: %s", getattr(p, "name", "?"), exc)
    # Cap per capability so a single gap doesn't flood the result.
    by_cap: dict[str, int] = {}
    capped: list[CourseMatch] = []
    for m in matches:
        k = m.capability.lower()
        if by_cap.get(k, 0) >= per_capability_cap:
            continue
        by_cap[k] = by_cap.get(k, 0) + 1
        capped.append(m)
    return capped


def enrich_transition_result(result: dict[str, Any]) -> dict[str, Any]:
    """Attach `recommended_training` to each upskilling-gap item, in place.

    Safe and idempotent: a no-op when recommendations are disabled or there are
    no gaps to match. Never raises.
    """
    if not getattr(settings, "training_recommendations_enabled", True):
        return result
    try:
        for opt in result.get("transition_options") or []:
            for gap in opt.get("upskilling_gap") or []:
                cap = gap.get("capability")
                if not cap:
                    continue
                matches = recommend_for_capabilities([cap], context={"option_role": opt.get("role")})
                gap["recommended_training"] = [m.as_dict() for m in matches]
    except Exception as exc:  # noqa: BLE001
        logger.warning("training enrichment failed (transition result kept): %s", exc)
    return result
