"""Feature flag management for controlled rollout and A/B testing."""
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class FeatureFlag(str, Enum):
    """Available feature flags."""

    # Conversational AI features
    ENHANCED_AGENTS = "enhanced_agents"  # Enhanced agent with memory
    AGENT_ACTIONS = "agent_actions"  # Agent action execution
    STREAMING_PROGRESS = "streaming_progress"  # SSE streaming for progress
    ACTION_CONFIRMATION = "action_confirmation"  # Require confirmation for actions

    # AI Safety features
    GOVERNANCE_GATES = "governance_gates"  # Governance validation
    HUMAN_REVIEW = "human_review"  # Human review workflow

    # Analytics features
    ANALYTICS_TRACKING = "analytics_tracking"  # Track user analytics
    PERFORMANCE_MONITORING = "performance_monitoring"  # Monitor performance

    # Onboarding features
    ONBOARDING_FLOW = "onboarding_flow"  # User onboarding workflow
    HELP_SYSTEM = "help_system"  # In-app help system

    # Beta features
    AUTONOMOUS_MODE = "autonomous_mode"  # Full autonomous operation
    MULTI_AGENT_COORDINATION = "multi_agent_coordination"  # Agents coordinating


class FeatureFlagManager:
    """Manage feature flags and their rollout."""

    # Default flags enabled
    DEFAULT_FLAGS = {
        FeatureFlag.ENHANCED_AGENTS: True,
        FeatureFlag.AGENT_ACTIONS: True,
        FeatureFlag.STREAMING_PROGRESS: True,
        FeatureFlag.ACTION_CONFIRMATION: True,
        FeatureFlag.GOVERNANCE_GATES: True,
        FeatureFlag.HUMAN_REVIEW: True,
        FeatureFlag.ANALYTICS_TRACKING: True,
        FeatureFlag.PERFORMANCE_MONITORING: False,  # Beta
        FeatureFlag.ONBOARDING_FLOW: False,  # Beta
        FeatureFlag.HELP_SYSTEM: False,  # Beta
        FeatureFlag.AUTONOMOUS_MODE: False,  # Beta
        FeatureFlag.MULTI_AGENT_COORDINATION: False,  # Beta
    }

    # Per-user flag overrides
    _user_overrides: dict[str, dict[str, bool]] = {}

    # Per-role flag overrides
    _role_overrides: dict[str, dict[str, bool]] = {}

    @classmethod
    def is_enabled(
        cls,
        flag: FeatureFlag,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> bool:
        """Check if a feature flag is enabled.

        Args:
            flag: Feature flag to check
            user_id: User ID (for per-user overrides)
            user_role: User role (for per-role overrides)

        Returns:
            True if flag is enabled for the user
        """
        # Check per-user override
        if user_id and user_id in cls._user_overrides:
            if flag.value in cls._user_overrides[user_id]:
                return cls._user_overrides[user_id][flag.value]

        # Check per-role override
        if user_role and user_role in cls._role_overrides:
            if flag.value in cls._role_overrides[user_role]:
                return cls._role_overrides[user_role][flag.value]

        # Check default
        return cls.DEFAULT_FLAGS.get(flag, False)

    @classmethod
    def enable_for_user(cls, flag: FeatureFlag, user_id: str) -> None:
        """Enable a flag for a specific user.

        Args:
            flag: Feature flag
            user_id: User ID
        """
        if user_id not in cls._user_overrides:
            cls._user_overrides[user_id] = {}
        cls._user_overrides[user_id][flag.value] = True
        logger.info(
            f"Enabled {flag.value} for user {user_id}",
            extra={"flag": flag.value, "user_id": user_id},
        )

    @classmethod
    def disable_for_user(cls, flag: FeatureFlag, user_id: str) -> None:
        """Disable a flag for a specific user.

        Args:
            flag: Feature flag
            user_id: User ID
        """
        if user_id not in cls._user_overrides:
            cls._user_overrides[user_id] = {}
        cls._user_overrides[user_id][flag.value] = False
        logger.info(
            f"Disabled {flag.value} for user {user_id}",
            extra={"flag": flag.value, "user_id": user_id},
        )

    @classmethod
    def enable_for_role(cls, flag: FeatureFlag, role: str) -> None:
        """Enable a flag for a specific role.

        Args:
            flag: Feature flag
            role: User role (admin, recruiter, candidate)
        """
        if role not in cls._role_overrides:
            cls._role_overrides[role] = {}
        cls._role_overrides[role][flag.value] = True
        logger.info(
            f"Enabled {flag.value} for role {role}",
            extra={"flag": flag.value, "role": role},
        )

    @classmethod
    def disable_for_role(cls, flag: FeatureFlag, role: str) -> None:
        """Disable a flag for a specific role.

        Args:
            flag: Feature flag
            role: User role
        """
        if role not in cls._role_overrides:
            cls._role_overrides[role] = {}
        cls._role_overrides[role][flag.value] = False
        logger.info(
            f"Disabled {flag.value} for role {role}",
            extra={"flag": flag.value, "role": role},
        )

    @classmethod
    def get_user_flags(cls, user_id: str, user_role: str) -> dict[str, bool]:
        """Get all feature flags for a user.

        Args:
            user_id: User ID
            user_role: User role

        Returns:
            Dict of all feature flags and their status for the user
        """
        flags = {}
        for flag in FeatureFlag:
            flags[flag.value] = cls.is_enabled(flag, user_id, user_role)
        return flags
