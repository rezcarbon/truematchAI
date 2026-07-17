"""Routes users to appropriate agents based on role and intent."""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.agents.agent_factory import AgentFactory


async def get_agent_for_user(
    user_id: UUID,
    user_role: str,
    db: AsyncSession,
    company_id: Optional[UUID] = None,
) -> BaseAgent:
    """Get the appropriate agent for a user based on their role.

    Loads customizable agent configuration from database if available,
    falls back to hardcoded defaults if no configuration found.

    Args:
        user_id: User's ID
        user_role: User's role (admin, recruiter, candidate)
        db: Database session
        company_id: Company ID for looking up custom agent config

    Returns:
        Appropriate agent instance, with custom config injected if available
    """
    # If no company_id provided, generate a default one
    # (In production, this would come from user.company_id or request context)
    if company_id is None:
        company_id = UUID("00000000-0000-0000-0000-000000000000")

    # Use factory to load agent with custom configuration
    factory = AgentFactory(db)

    try:
        # For recruiters, use M Agent with custom config fallback
        if user_role == "recruiter":
            from app.agents.m_agent_wrapper import MAgentRecruiterWrapper
            agent = MAgentRecruiterWrapper()
            # Try to inject custom config
            try:
                config = await factory.config_service.get_active_config(
                    company_id, "recruiter"
                )
                if config:
                    agent = factory._apply_config_to_agent(agent, config)
            except Exception:
                pass  # Fall back to default M Agent
            return agent

        # For admin and candidate, use factory to load customizable agents
        return await factory.get_agent_for_user(user_id, user_role, company_id)

    except Exception as e:
        # If factory fails, fall back to hardcoded agents
        print(f"Warning: Agent factory failed, using hardcoded defaults: {e}")
        if user_role == "admin":
            from app.agents.admin_agent import AdminAgent
            return AdminAgent()
        elif user_role == "recruiter":
            from app.agents.m_agent_wrapper import MAgentRecruiterWrapper
            return MAgentRecruiterWrapper()
        elif user_role == "candidate":
            from app.agents.candidate_agent import CandidateAgent
            return CandidateAgent()
        else:
            from app.agents.candidate_agent import CandidateAgent
            return CandidateAgent()


async def route_to_agent(
    message: str,
    user_role: str,
    conversation_history: list[dict],
) -> str:
    """Route a message to the appropriate agent based on intent.

    This function analyzes the user message and conversation history
    to determine which agent should handle it.

    Args:
        message: User message
        user_role: User's role
        conversation_history: Previous conversation turns

    Returns:
        Name of the agent to route to
    """
    # For now, route purely by user role
    # In advanced implementation, would use intent recognition
    # via Claude to analyze message and route accordingly

    return {
        "admin": "admin_agent",
        "recruiter": "recruiter_agent",
        "candidate": "candidate_agent",
    }.get(user_role, "candidate_agent")
