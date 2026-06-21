"""Routes users to appropriate agents based on role and intent."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.admin_agent import AdminAgent
from app.agents.recruiter_agent import RecruiterAgent
from app.agents.candidate_agent import CandidateAgent
from app.agents.base_agent import BaseAgent


async def get_agent_for_user(
    user_id: UUID,
    user_role: str,
    db: AsyncSession,
) -> BaseAgent:
    """Get the appropriate agent for a user based on their role.

    Args:
        user_id: User's ID
        user_role: User's role (admin, recruiter, candidate)
        db: Database session

    Returns:
        Appropriate agent instance
    """
    if user_role == "admin":
        return AdminAgent()
    elif user_role == "recruiter":
        return RecruiterAgent()
    elif user_role == "candidate":
        return CandidateAgent()
    else:
        # Default to candidate agent for unknown roles
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
