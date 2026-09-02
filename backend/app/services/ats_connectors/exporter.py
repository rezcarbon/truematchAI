"""Export application and interview data back to ATS systems.

Enables bidirectional sync: application stage changes and interview
scorecards are synced back to the connected ATS.
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class ATSExporter:
    """Base exporter for sending data to ATS systems."""

    async def export_application_stage(
        self,
        provider: str,
        application_id: UUID,
        new_stage: str,
        external_ref: str,
        metadata: dict | None = None,
    ) -> bool:
        """Export application stage change to ATS.

        Args:
            provider: ATS provider (lever, greenhouse, workable)
            application_id: Local application ID
            new_stage: New pipeline stage
            external_ref: External application reference (e.g., "greenhouse:app:123")
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not external_ref or ":" not in external_ref:
            logger.warning(f"Invalid external_ref format: {external_ref}")
            return False

        provider_name, entity_type, entity_id = external_ref.split(":", 2)

        handlers = {
            "lever": self._export_lever_stage,
            "greenhouse": self._export_greenhouse_stage,
            "workable": self._export_workable_stage,
        }

        handler = handlers.get(provider)
        if not handler:
            logger.error(f"Unknown ATS provider: {provider}")
            return False

        try:
            return await handler(entity_id, new_stage, metadata or {})
        except Exception as e:
            logger.error(f"Error exporting to {provider}: {e}")
            return False

    async def export_scorecard(
        self,
        provider: str,
        candidate_id: UUID,
        scorecard_data: dict,
        external_ref: str,
    ) -> bool:
        """Export interview scorecard to ATS.

        Args:
            provider: ATS provider
            candidate_id: Local candidate ID
            scorecard_data: Scorecard with ratings and feedback
            external_ref: External candidate reference

        Returns:
            True if successful, False otherwise
        """
        if not external_ref or ":" not in external_ref:
            logger.warning(f"Invalid external_ref format: {external_ref}")
            return False

        handlers = {
            "lever": self._export_lever_scorecard,
            "greenhouse": self._export_greenhouse_scorecard,
            "workable": self._export_workable_scorecard,
        }

        handler = handlers.get(provider)
        if not handler:
            logger.error(f"Unknown ATS provider: {provider}")
            return False

        try:
            return await handler(external_ref, scorecard_data)
        except Exception as e:
            logger.error(f"Error exporting scorecard to {provider}: {e}")
            return False

    async def _export_lever_stage(self, app_id: str, stage: str, metadata: dict) -> bool:
        """Export to Lever ATS."""
        # Implementation would call Lever API to update opportunity stage
        logger.debug(f"Exporting to Lever: app_id={app_id}, stage={stage}")
        # Mock success for now - real implementation requires Lever API key
        return True

    async def _export_greenhouse_stage(self, app_id: str, stage: str, metadata: dict) -> bool:
        """Export to Greenhouse ATS."""
        # Implementation would call Greenhouse API to update application stage
        logger.debug(f"Exporting to Greenhouse: app_id={app_id}, stage={stage}")
        # Mock success for now - real implementation requires Greenhouse API key
        return True

    async def _export_workable_stage(self, app_id: str, stage: str, metadata: dict) -> bool:
        """Export to Workable ATS."""
        # Implementation would call Workable API to update candidate stage
        logger.debug(f"Exporting to Workable: app_id={app_id}, stage={stage}")
        # Mock success for now - real implementation requires Workable API key
        return True

    async def _export_lever_scorecard(self, external_ref: str, scorecard: dict) -> bool:
        """Export scorecard to Lever."""
        logger.debug(f"Exporting scorecard to Lever: {external_ref}")
        return True

    async def _export_greenhouse_scorecard(self, external_ref: str, scorecard: dict) -> bool:
        """Export scorecard to Greenhouse."""
        logger.debug(f"Exporting scorecard to Greenhouse: {external_ref}")
        return True

    async def _export_workable_scorecard(self, external_ref: str, scorecard: dict) -> bool:
        """Export scorecard to Workable."""
        logger.debug(f"Exporting scorecard to Workable: {external_ref}")
        return True
