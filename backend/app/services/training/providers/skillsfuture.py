"""SkillsFuture SG provider — a SECOND catalog-backed partner.

Demonstrates the modular path end-to-end: a new partner is just a provider class
+ its own catalog + a config flag + one registration line. Its results merge with
(and de-duplicate against) every other enabled provider. Catalog-backed today
(`catalogs/skillsfuture_catalog.json`); swap `match()` for a live API call the
same way the NTUC stub documents.
"""
from __future__ import annotations

from typing import Any

from app.config import settings
from app.services.training.base import CourseMatch
from app.services.training.catalog import match_catalog


class SkillsFutureProvider:
    name = "skillsfuture"

    def enabled(self) -> bool:
        return bool(getattr(settings, "skillsfuture_enabled", True))

    def match(self, capabilities: list[str], context: dict[str, Any]) -> list[CourseMatch]:
        return match_catalog("skillsfuture_catalog.json", capabilities, default_provider="SkillsFuture SG")
