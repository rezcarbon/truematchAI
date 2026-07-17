"""Factory for instantiating agents with database-driven configuration.

The factory pattern allows agents to be loaded from the database instead of
being hardcoded. This enables:
- Custom instructions per workspace
- Per-agent tool configuration
- Versioning and rollback
- A/B testing different agent configs

Falls back gracefully to hardcoded defaults if no config exists.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.admin_agent import AdminAgent
from app.agents.candidate_agent import CandidateAgent
from app.agents.recruiter_agent import RecruiterAgent
from app.models import AgentConfig, AgentConfigStatus
from app.services.agent_config_service import AgentConfigService


class AgentFactory:
    """Factory for creating agent instances with customizable configuration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_service = AgentConfigService(db)

    async def get_agent_for_user(
        self,
        user_id: uuid.UUID,
        user_role: str,
        company_id: uuid.UUID,
        agent_type: Optional[str] = None,
    ) -> AdminAgent | RecruiterAgent | CandidateAgent:
        """Get the appropriate agent for a user, with customized configuration.

        Args:
            user_id: ID of the user requesting the agent
            user_role: Role of the user (admin, recruiter, candidate)
            company_id: ID of the company
            agent_type: Specific agent type to load (optional, defaults to user_role)

        Returns:
            Configured agent instance (AdminAgent, RecruiterAgent, or CandidateAgent)

        This method:
        1. Determines which agent type to use (based on agent_type or user_role)
        2. Loads the active configuration from database (if available)
        3. Falls back to default hardcoded agent if no config found
        4. Injects custom instructions and tools into the agent
        """
        agent_type_to_use = agent_type or user_role

        # Load custom config from database
        config = await self._load_active_config(company_id, agent_type_to_use)

        # Instantiate base agent
        agent = self._instantiate_base_agent(user_role)

        # If we have a custom config, inject it
        if config:
            agent = self._apply_config_to_agent(agent, config)

        return agent

    async def _load_active_config(
        self, company_id: uuid.UUID, agent_type: str
    ) -> Optional[AgentConfig]:
        """Load the active configuration for an agent from database.

        Returns None if no active config found (graceful fallback to defaults).
        """
        try:
            return await self.config_service.get_active_config(company_id, agent_type)
        except Exception as e:
            # If database is down or there's an error, just return None
            # and the agent will use hardcoded defaults
            print(f"Warning: Failed to load agent config from database: {e}")
            return None

    def _instantiate_base_agent(self, user_role: str) -> AdminAgent | RecruiterAgent | CandidateAgent:
        """Instantiate a base agent for the given role."""
        if user_role == "admin":
            return AdminAgent()
        elif user_role == "recruiter":
            return RecruiterAgent()
        elif user_role == "candidate":
            return CandidateAgent()
        else:
            # Default to candidate for unknown roles
            return CandidateAgent()

    def _apply_config_to_agent(
        self,
        agent: AdminAgent | RecruiterAgent | CandidateAgent,
        config: AgentConfig,
    ) -> AdminAgent | RecruiterAgent | CandidateAgent:
        """Apply custom configuration to an agent instance.

        Injects:
        - Custom instructions (system prompt)
        - Available tools
        - Tool-specific parameters
        - Agent-wide parameters (temperature, model, etc.)
        """
        # Override instructions
        if config.instructions:
            agent.instructions = config.instructions

        # Override available tools (if agent supports it)
        if hasattr(agent, "tools_enabled"):
            agent.tools_enabled = config.tools_enabled
        if hasattr(agent, "tool_parameters"):
            agent.tool_parameters = config.tool_parameters

        # Override agent parameters (temperature, model, etc.)
        if hasattr(agent, "agent_parameters"):
            agent.agent_parameters = config.agent_parameters

        # Store config reference for logging
        agent._config_id = config.id
        agent._config_version = config.version_number

        return agent


__all__ = ["AgentFactory"]
