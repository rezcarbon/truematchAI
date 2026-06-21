"""NTUC LearningHub provider — example of a pluggable EXTERNAL partner.

This is the template for adding any training partner with a live catalog/API:

    1. Implement `enabled()` to gate on the partner's credentials/flag.
    2. Implement `match()` to query the partner and map results to CourseMatch.
    3. Register it in `app/services/training/__init__.py`.
    4. Add the config flag(s) in `app/config.py` + `.env.example`.

It is a SAFE NO-OP until configured (returns []), so shipping it changes
nothing until the integration is switched on — mirroring the platform's other
gated integrations. When credentials are present, replace the body of `match()`
with a real catalog lookup.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import settings
from app.services.training.base import CourseMatch

logger = logging.getLogger("truematch.training.ntuc")


class NTUCLearningHubProvider:
    name = "ntuc_learninghub"

    def enabled(self) -> bool:
        # Enabled only when explicitly switched on AND an API base/key is present.
        return bool(
            getattr(settings, "ntuc_learninghub_enabled", False)
            and getattr(settings, "ntuc_learninghub_api_base", "")
        )

    def match(self, capabilities: list[str], context: dict[str, Any]) -> list[CourseMatch]:
        if not self.enabled():
            return []
        # --- Integration point -------------------------------------------------
        # A real implementation queries the partner's course API by capability and
        # maps each result into CourseMatch(capability=..., title=..., provider=
        # "NTUC LearningHub", url=..., format=..., duration_weeks=..., level=...,
        # relevance=...). Guard network errors and return [] on failure so the
        # transition pipeline never breaks on a partner outage.
        # ----------------------------------------------------------------------
        logger.debug("NTUC LearningHub enabled but live lookup not yet implemented; returning []")
        return []
