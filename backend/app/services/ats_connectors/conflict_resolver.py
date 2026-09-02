"""Detect and resolve conflicts between local and ATS data.

When syncing bidirectionally, conflicts can occur if both systems
are modified concurrently. This module provides conflict detection
and resolution strategies.
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Literal

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts."""

    LOCAL_WINS = "local_wins"  # Prefer local changes
    ATS_WINS = "ats_wins"  # Prefer ATS changes
    MANUAL = "manual"  # Require manual resolution
    MERGE = "merge"  # Merge compatible changes


class ConflictDetector:
    """Detect conflicts between local and ATS versions."""

    @staticmethod
    def detect_application_conflict(
        local_stage: str,
        local_updated_at: datetime,
        ats_stage: str,
        ats_updated_at: datetime,
    ) -> bool:
        """Detect if application stage has conflicting changes.

        Args:
            local_stage: Local application stage
            local_updated_at: When local was last updated
            ats_stage: ATS application stage
            ats_updated_at: When ATS was last updated

        Returns:
            True if conflict detected, False otherwise
        """
        if local_stage == ats_stage:
            return False

        # If both were modified after sync was initiated, it's a conflict
        return local_updated_at != ats_updated_at and local_stage != ats_stage

    @staticmethod
    def detect_scorecard_conflict(
        local_score: dict,
        local_updated_at: datetime,
        ats_feedback: dict | None,
        ats_updated_at: datetime | None,
    ) -> bool:
        """Detect if scorecard has conflicting changes.

        Args:
            local_score: Local scorecard data
            local_updated_at: When local was last updated
            ats_feedback: ATS scorecard feedback (if any)
            ats_updated_at: When ATS feedback was added

        Returns:
            True if conflict detected, False otherwise
        """
        if not ats_feedback:
            return False  # No conflict if ATS has no feedback

        if not ats_updated_at:
            return False

        # Conflict if both have feedback and both were modified
        return local_updated_at != ats_updated_at

    @staticmethod
    def resolve_conflict(
        strategy: ConflictResolutionStrategy | str,
        local_value: str | dict,
        ats_value: str | dict,
        local_timestamp: datetime,
        ats_timestamp: datetime,
    ) -> str | dict:
        """Resolve conflict using specified strategy.

        Args:
            strategy: Resolution strategy to use
            local_value: Local version
            ats_value: ATS version
            local_timestamp: When local was modified
            ats_timestamp: When ATS was modified

        Returns:
            Resolved value
        """
        strategy = ConflictResolutionStrategy(strategy)

        if strategy == ConflictResolutionStrategy.LOCAL_WINS:
            logger.info("Conflict resolution: local_wins")
            return local_value

        elif strategy == ConflictResolutionStrategy.ATS_WINS:
            logger.info("Conflict resolution: ats_wins")
            return ats_value

        elif strategy == ConflictResolutionStrategy.MERGE:
            # Try to merge if both are dicts
            if isinstance(local_value, dict) and isinstance(ats_value, dict):
                merged = {**ats_value, **local_value}
                logger.info("Conflict resolution: merged")
                return merged
            # Fall back to most recent
            logger.info("Conflict resolution: merge fallback to most_recent")
            return local_value if local_timestamp > ats_timestamp else ats_value

        else:  # MANUAL
            logger.warning("Conflict requires manual resolution")
            raise ValueError("Conflict requires manual resolution - cannot auto-resolve")

    @staticmethod
    def get_suggested_resolution(
        local_value: str | dict,
        ats_value: str | dict,
        local_timestamp: datetime,
        ats_timestamp: datetime,
    ) -> ConflictResolutionStrategy:
        """Suggest automatic resolution strategy based on conflict analysis.

        Args:
            local_value: Local version
            ats_value: ATS version
            local_timestamp: When local was modified
            ats_timestamp: When ATS was modified

        Returns:
            Suggested strategy
        """
        # If they're the same, no conflict
        if local_value == ats_value:
            return ConflictResolutionStrategy.LOCAL_WINS

        # If local is newer, prefer local
        if local_timestamp > ats_timestamp:
            return ConflictResolutionStrategy.LOCAL_WINS

        # If ATS is newer, prefer ATS
        if ats_timestamp > local_timestamp:
            return ConflictResolutionStrategy.ATS_WINS

        # If timestamps are the same, require manual
        return ConflictResolutionStrategy.MANUAL
