"""Enhanced agent with action execution and session memory integration."""
from __future__ import annotations

import asyncio
import logging
import uuid
from abc import abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.action_executor import ActionExecutor
from app.agents.agent_tools import tools_for_role, tool_calls_to_actions
from app.agents.base_agent import _DASHBOARD_PROTOCOL
from app.agents.base_agent import BaseAgent, AgentResponse
from app.agents.session_memory import SessionMemory
from app.agents.session_memory_manager import SessionMemoryManager
from app.engines.client import call_claude_with_tools, is_live
from app.models.user import User
from app.models.autonomous_settings import AutonomousSettings
from app.core.feature_flags import FeatureFlagManager, FeatureFlag

logger = logging.getLogger(__name__)


class EnhancedBaseAgent(BaseAgent):
    """Agent with session memory and action execution capabilities."""

    async def respond(
        self,
        message: str,
        history: list[dict],
        user: User,
        db: AsyncSession,
        session_id: Optional[uuid.UUID] = None,
    ) -> AgentResponse:
        """Generate response with memory and action execution.

        Args:
            message: User message
            history: Conversation history
            user: User object
            db: Database session
            session_id: Chat session ID for memory persistence

        Returns:
            AgentResponse with text, actions, and suggestions
        """
        try:
            # Load session memory
            if not session_id:
                logger.warning(
                    "No session_id provided, creating new memory",
                    extra={"user_id": str(user.id)},
                )
                memory = SessionMemory(str(user.id))
            else:
                memory = await SessionMemoryManager.get_or_create(session_id, db)

            # Load user context
            user_context = await self._get_user_context(user, db)

            # Load role-specific context
            rich_context = await self._load_role_context(user, db)
            user_context.update(rich_context)

            # Update memory with focus on current message
            memory.update_focus(message[:50])  # First 50 chars as focus
            memory.increment_message_count()
            memory.set_state("processing")

            # Build enriched system prompt
            system_prompt = self._build_rich_system_prompt(user_context, memory)

            # Get response from Claude with native tool-use: the model decides
            # whether to call one of the role-scoped action tools, returning both
            # natural-language text and structured (validated) tool calls. Falls
            # back to a context-aware mock when no API key is configured.
            response_text, actions = await self._complete_with_tools(
                system=system_prompt,
                message=message,
                history=history,
                user=user,
                user_context=user_context,
            )

            # Check if autonomous mode is enabled for this user
            is_autonomous = FeatureFlagManager.is_enabled(
                FeatureFlag.AUTONOMOUS_MODE,
                user_id=str(user.id),
                user_role=user.role,
            )

            # Load autonomous settings if enabled
            if is_autonomous:
                stmt = select(AutonomousSettings).where(AutonomousSettings.user_id == user.id)
                result = await db.execute(stmt)
                settings = result.scalar_one_or_none()
                if settings and settings.enabled:
                    logger.info(
                        "Autonomous mode enabled for user",
                        extra={
                            "user_id": str(user.id),
                            "action_count": len(actions),
                            "confidence_threshold": settings.min_confidence_threshold,
                        },
                    )
                else:
                    is_autonomous = False

            # Execute actions
            # In autonomous mode, actions execute directly
            # In manual mode, they're marked pending for user confirmation
            executed_actions = await ActionExecutor.execute_actions(
                actions,
                user,
                db,
                autonomous=is_autonomous,
            )

            # Update memory with action results
            for action in executed_actions:
                memory.record_action(
                    action_id=action.get("id", "unknown"),
                    description=action.get("description", ""),
                    status=action.get("status", "completed"),
                )

            # Generate suggestions based on context
            suggestions = self._generate_suggestions(user_context, executed_actions)

            # Save memory
            if session_id:
                memory.set_state("idle")
                await SessionMemoryManager.save(session_id, memory, db)

            logger.info(
                "Agent response generated",
                extra={
                    "user_id": str(user.id),
                    "session_id": str(session_id),
                    "action_count": len(executed_actions),
                    "memory_message_count": memory.context["metadata"]["message_count"],
                },
            )

            return AgentResponse(
                text=response_text,
                actions=executed_actions,
                suggestions=suggestions,
            )

        except Exception as e:
            logger.error(
                f"Error in agent response generation: {e}",
                extra={"user_id": str(user.id)},
            )
            # Return error response without crashing
            return AgentResponse(
                text=f"I encountered an error: {str(e)}. Please try again.",
                actions=[],
                suggestions=[],
            )

    async def prepare_turn(
        self, message: str, user: User, db: AsyncSession
    ) -> tuple[str, dict]:
        """Build the enriched system prompt + user context for one turn.

        Exposed so the streaming endpoint can reuse the exact same role-aware
        context the non-streaming `respond()` path builds, without duplicating
        the context-loading logic.
        """
        user_context = await self._get_user_context(user, db)
        rich_context = await self._load_role_context(user, db)
        user_context.update(rich_context)
        memory = SessionMemory(str(user.id))
        memory.update_focus(message[:50])
        system_prompt = self._build_rich_system_prompt(user_context, memory)
        return system_prompt, user_context

    async def _complete_with_tools(
        self,
        system: str,
        message: str,
        history: list[dict],
        user: User,
        user_context: dict,
    ) -> tuple[str, list[dict]]:
        """Generate a reply with native tool-use.

        Returns ``(text, actions)`` where ``actions`` are structured action
        dicts derived from the model's tool calls (ready for ActionExecutor).
        Mock mode returns a context-aware reply with no actions.
        """
        if not is_live():
            return self._mock_reply(message, user_context), []

        tools = tools_for_role(user.role)

        def _call() -> tuple[str, list[dict]]:
            return call_claude_with_tools(
                system=system,
                user_content=message,
                tools=tools,
                history=history,
                max_tokens=1024,
            )

        try:
            text, tool_calls = await asyncio.to_thread(_call)
        except Exception as exc:  # noqa: BLE001
            # Degrade gracefully when the live API is unavailable (network,
            # rate-limit, or — commonly in local/demo — an exhausted credit
            # balance) rather than surfacing a raw error to the user.
            logger.warning("LLM call failed, falling back to mock reply: %s", exc)
            return self._mock_reply(message, user_context), []

        actions = tool_calls_to_actions(tool_calls)
        if not text and actions:
            text = "I've prepared the following action(s) for your review:"
        elif not text:
            text = "Done."
        return text, actions

    async def _complete(
        self,
        system: str,
        message: str,
        history: list[dict],
        user_context: dict,
    ) -> str:
        """Produce an assistant reply.

        Uses the live Claude API when an API key is configured; otherwise falls
        back to a deterministic, context-aware mock so the conversational
        interface stays functional in local/offline deployments (mirrors the
        mock-fallback pattern used by the training chat engine).
        """
        if not is_live():
            return self._mock_reply(message, user_context)

        # ClaudeClient.analyze is synchronous; run it off the event loop.
        def _call() -> str:
            convo = "\n".join(
                f"{turn.get('role', 'user')}: {turn.get('content', '')}"
                for turn in (history or [])[-6:]
            )
            prompt = (
                f"{convo}\n\nuser: {message}" if convo else message
            )
            return self.client.analyze(prompt, system=system, max_tokens=1024)

        return await asyncio.to_thread(_call)

    def _mock_reply(self, message: str, user_context: dict) -> str:
        """Context-aware deterministic reply used when no LLM key is set.

        Surfaces the role-specific data the agent loaded so the chat still
        demonstrates real platform integration rather than a canned string.
        """
        name = user_context.get("name", "there")
        role = user_context.get("role", "user")
        role_label = getattr(role, "value", str(role))

        lines = [f"Hi {name} — I'm your TrueMatch {role_label} assistant."]

        gov = user_context.get("governance")
        users = user_context.get("users")
        positions = user_context.get("positions") or user_context.get("open_positions")
        pipeline = user_context.get("pipeline")
        resumes = user_context.get("resumes") or user_context.get("my_resumes")

        if isinstance(users, dict) and users.get("total") is not None:
            lines.append(
                f"Platform users: {users.get('total', 0)} "
                f"({users.get('admin', 0)} admin, {users.get('recruiter', 0)} recruiter, "
                f"{users.get('candidate', 0)} candidate)."
            )
        if isinstance(gov, dict) and gov.get("total") is not None:
            lines.append(
                f"Governance reviews: {gov.get('pending', 0)} pending, "
                f"{gov.get('total', 0)} total."
            )
        if positions is not None:
            count = positions if isinstance(positions, int) else len(positions)
            lines.append(f"Open positions visible to you: {count}.")
        if pipeline is not None:
            count = pipeline if isinstance(pipeline, int) else len(pipeline)
            lines.append(f"Candidates in your pipeline: {count}.")
        if resumes is not None:
            count = resumes if isinstance(resumes, int) else len(resumes)
            lines.append(f"Your uploaded resumes: {count}.")

        lines.append(
            "\n(Note: the language model isn't configured on this deployment, "
            "so I'm answering from live platform data with a templated reply. "
            "Set ANTHROPIC_API_KEY for full conversational responses.)"
        )
        return "\n".join(lines)

    def _build_rich_system_prompt(
        self, user_context: dict, memory: SessionMemory
    ) -> str:
        """Build system prompt with context and memory."""
        memory_context = memory.get_context()
        durable = user_context.get("durable_memory") or ""
        durable_block = (
            f"\nDURABLE MEMORY (curated across past sessions — apply silently, "
            f"correct it if the user contradicts it):\n{durable}\n"
            if durable
            else ""
        )
        return f"""{self.instructions}

USER CONTEXT:
- Role: {user_context.get('role', 'unknown')}
- Name: {user_context.get('name', 'unknown')}
- User ID: {user_context.get('user_id', 'unknown')}
{durable_block}
SESSION MEMORY:
- Current Focus: {memory_context.get('current_focus', 'None')}
- Conversation State: {memory_context.get('conversation_state', 'idle')}
- Message Count: {memory_context['metadata'].get('message_count', 0)}
- Active Resources: {list(memory_context.get('active_resources', {}).keys()) or 'None'}

ROLE-SPECIFIC CONTEXT:
{self._format_context(user_context)}

GUIDELINES:
1. Use session memory to maintain conversation continuity
2. Reference previous actions and focus areas
3. Always explain your reasoning
4. Ask for confirmation before significant actions
5. Reference previous context when relevant
6. Suggest proactive next steps
7. When a request is ambiguous or missing a parameter you need to act
   (which position? which candidates? what time? notify whom?), call the
   `clarify` tool to ASK FIRST — never guess a value and never emit a
   multi-step `plan` built on assumptions. Offer suggested answers in the
   clarify `options` when you can. Only plan/act once the goal is unambiguous.

CONVERSATION STYLE:
- Natural and friendly
- Professional but conversational
- Remember what the user is working on
- Acknowledge previous messages in this session
- Admit what you don't know
{_DASHBOARD_PROTOCOL}
"""

    @abstractmethod
    async def _load_role_context(self, user: User, db: AsyncSession) -> dict:
        """Load role-specific context data.

        Should be overridden by subclasses to load:
        - Recruiter: open jobs, pending candidates, pipeline metrics
        - Candidate: uploaded CVs, applied jobs, recommendations
        - Admin: system metrics, pending reviews, user counts

        Args:
            user: User object
            db: Database session

        Returns:
            Dict with role-specific context data
        """
        return {}

    @abstractmethod
    def _format_context(self, user_context: dict) -> str:
        """Format role-specific context for system prompt."""
        return ""
