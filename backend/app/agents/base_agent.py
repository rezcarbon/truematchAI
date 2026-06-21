"""Base agent class for all conversational agents."""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.client import ClaudeClient
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class Action:
    """An action the agent will execute."""
    id: str
    description: str
    status: str = "pending"  # pending, completed, failed
    result: Optional[str] = None


@dataclass
class AgentResponse:
    """Response from an agent."""
    text: str
    actions: list[dict] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Base class for all conversational agents."""

    def __init__(self, role: str, instructions: str):
        self.role = role
        self.instructions = instructions
        self.client = ClaudeClient()

    @abstractmethod
    async def respond(
        self,
        message: str,
        history: list[dict],
        user: User,
        db: AsyncSession,
        session_id: Optional[uuid.UUID] = None,
    ) -> AgentResponse:
        """Generate a response to user message.

        Args:
            message: User's message
            history: Previous conversation turns
            user: User object with role, id, etc.
            db: Database session for loading context
            session_id: Chat session ID for memory persistence

        Returns:
            AgentResponse with text, actions, and suggestions
        """
        pass

    def _build_system_prompt(self, user_context: dict) -> str:
        """Build system prompt with agent instructions + user context."""
        return f"""{self.instructions}

USER CONTEXT:
- Role: {user_context.get('role', 'unknown')}
- User ID: {user_context.get('user_id', 'unknown')}

GUIDELINES:
1. Be helpful, clear, and proactive
2. Always explain your reasoning
3. Ask for confirmation before taking significant actions
4. Reference previous context when relevant
5. Suggest next steps at the end of responses

CONVERSATION STYLE:
- Natural and friendly
- Professional but conversational
- Admit what you don't know
- Ask clarifying questions when needed
"""

    def _parse_actions_from_response(self, response: str) -> list[dict]:
        """Extract action markers from response text.

        Looks for [ACTION: description] patterns in the response.
        """
        actions = []
        import re

        # Find all [ACTION: ...] patterns
        matches = re.findall(r"\[ACTION: ([^\]]+)\]", response)
        for i, match in enumerate(matches):
            actions.append({
                "id": f"action_{i}",
                "description": match,
                "status": "pending",
            })

        return actions

    def _generate_suggestions(self, context: dict, actions: list) -> list[str]:
        """Generate suggestions for next steps."""
        suggestions = []

        # Add role-specific suggestions
        if self.role == "recruiter":
            suggestions.extend([
                "Upload candidate resumes",
                "Schedule interviews",
                "Check pipeline status",
            ])
        elif self.role == "candidate":
            suggestions.extend([
                "Find matching jobs",
                "Improve your CV",
                "Track applications",
            ])
        elif self.role == "admin":
            suggestions.extend([
                "Review governance status",
                "Check system metrics",
                "Manage users",
            ])

        return suggestions[:3]  # Return top 3

    async def _get_user_context(self, user: User, db: AsyncSession) -> dict:
        """Load context about the user for the agent."""
        from app.services.user_memory import fetch_memory_block

        try:
            durable_memory = await fetch_memory_block(db, user.id)
        except Exception:  # noqa: BLE001 — memory must never break a turn
            durable_memory = ""
        return {
            "user_id": str(user.id),
            "role": user.role,
            "name": user.display_name or user.email,
            "durable_memory": durable_memory,
        }
