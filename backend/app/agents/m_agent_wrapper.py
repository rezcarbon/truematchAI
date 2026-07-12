"""M Agent wrapper to integrate M Agent Layer 1 & 2 into TrueMatch chat endpoint.

This module bridges M Agent (from m-agent-hackathon) with TrueMatch's existing
chat infrastructure, providing:
- Intent-based routing (6 categories)
- Agentic loop with tool-result feedback
- Integrity analysis for candidates
- Governance gate integration
- Session persistence with multi-turn context

The wrapper maintains compatibility with existing Agent interface while
leveraging M Agent's advanced reasoning capabilities.
"""

import logging
import asyncio
from uuid import UUID
from typing import Optional, Callable, Awaitable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.chat import ChatMessage
from app.agents.base_agent import AgentResponse
from app.core.clock import utcnow

logger = logging.getLogger("truematch.agents.m_agent")


class MAgentRecruiterWrapper:
    """Wraps M Agent for recruiter role with full TrueMatch integration.

    This wrapper:
    1. Calls M Agent's agentic loop for recruiter queries
    2. Converts responses to TrueMatch AgentResponse format
    3. Handles streaming callbacks for SSE
    4. Manages session context and multi-turn history
    5. Logs governance events for compliance
    6. Captures learning data for agent improvement
    """

    def __init__(self):
        """Initialize the M Agent wrapper."""
        self.logger = logging.getLogger(__name__)
        self.m_agent_imported = False
        self._ensure_m_agent_available()

    def _ensure_m_agent_available(self) -> bool:
        """Verify M Agent is importable from m-agent-hackathon.

        Returns:
            True if M Agent available, False otherwise
        """
        try:
            # Try importing M Agent components
            from m_agent_hackathon.backend.app.agents.m_agent_recruiter import (
                run_recruiter_agent
            )
            self.run_recruiter_agent = run_recruiter_agent
            self.m_agent_imported = True
            self.logger.info("[M Agent] Import successful")
            return True
        except ImportError as e:
            self.logger.error(f"[M Agent] Import failed: {e}")
            self.logger.warning("[M Agent] M Agent layer unavailable - will fallback to local agent")
            self.m_agent_imported = False
            return False

    async def respond(
        self,
        message: str,
        history: list[dict],
        user: User,
        db: AsyncSession,
        session_id: UUID,
        mode: str = "general",
        candidate_context: Optional[dict] = None,
        stream_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> AgentResponse:
        """Execute M Agent with same interface as local agents.

        This is the main entry point called by the chat endpoint. It:
        1. Validates M Agent availability
        2. Prepares context (conversation history, session data)
        3. Calls M Agent's agentic loop
        4. Converts response to TrueMatch format
        5. Logs execution for learning/compliance
        6. Returns structured response

        Args:
            message: User's current message
            history: Conversation history (list of {role, content} dicts)
            user: Current User object
            db: Database session (AsyncSession)
            session_id: Chat session UUID
            mode: Chat mode (general, career_coach, interview_prep) - not used by M Agent
            candidate_context: Candidate context dict (not used by M Agent)
            stream_callback: Async callback for streaming token updates

        Returns:
            AgentResponse with text, actions, suggestions, metadata

        Raises:
            HTTPException: On critical errors (logged and returned to user)
        """
        start_time = datetime.utcnow()
        execution_context = {
            "user_id": str(user.id),
            "session_id": str(session_id),
            "user_role": user.role,
            "message_preview": message[:100],
            "history_length": len(history),
        }

        self.logger.info(
            f"[M Agent] Request initiated",
            extra=execution_context
        )

        try:
            # 1. VALIDATE M AGENT AVAILABILITY
            if not self.m_agent_imported:
                self.logger.warning("[M Agent] Not available - would use fallback here")
                # In production, would fallback to local agent
                # For now, raise so we know M Agent is needed
                raise ImportError("M Agent not available")

            # 2. PREPARE CONTEXT FOR M AGENT
            # M Agent expects multi-turn history in specific format
            m_agent_history = self._prepare_history(history)

            self.logger.debug(
                f"[M Agent] Context prepared",
                extra={
                    **execution_context,
                    "prepared_history_length": len(m_agent_history),
                }
            )

            # 3. CALL M AGENT WITH STREAMING CALLBACK
            # This is where M Agent's agentic loop executes:
            # - Classifies intent (6 categories)
            # - Loads conversation context
            # - Runs agentic loop (max 6 iterations)
            # - Executes tools and feeds results back
            # - Generates grounded response

            # Create streaming wrapper to capture tokens
            streamed_tokens = []

            async def capture_stream(chunk: str):
                """Capture streamed chunks for logging."""
                streamed_tokens.append(chunk)
                if stream_callback:
                    await stream_callback(chunk)

            response_text, pending_actions = await self.run_recruiter_agent(
                message=message,
                session_id=str(session_id),
                user_id=str(user.id),
                db=db,
                stream_callback=capture_stream,
            )

            # 4. CONVERT M AGENT RESPONSE TO TRUEMATCH FORMAT
            actions = self._convert_actions(pending_actions, user.id)
            suggestions = self._extract_suggestions(response_text, pending_actions)

            # 5. LOG EXECUTION FOR LEARNING & COMPLIANCE
            execution_data = {
                **execution_context,
                "token_count": len("".join(streamed_tokens).split()),
                "action_count": len(actions),
                "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
            }

            self.logger.info(
                f"[M Agent] Execution complete",
                extra=execution_data
            )

            # 6. LOG LEARNING DATA (for future agent improvement)
            await self._log_learning_data(
                user_id=user.id,
                session_id=session_id,
                message=message,
                response=response_text,
                actions=actions,
                suggestions=suggestions,
                execution_time_ms=execution_data["execution_time_ms"],
                db=db,
            )

            # 7. RETURN RESPONSE IN TRUEMATCH FORMAT
            return AgentResponse(
                text=response_text,
                actions=actions,
                suggestions=suggestions,
                metadata={
                    "agent": "m_agent",
                    "intent_classified": True,
                    "tools_executed": len(actions),
                    "streaming_supported": True,
                }
            )

        except Exception as e:
            self.logger.error(
                f"[M Agent] Error: {str(e)[:200]}",
                extra=execution_context,
                exc_info=True
            )
            raise

    def _prepare_history(self, history: list[dict]) -> list[dict]:
        """Prepare conversation history for M Agent.

        Converts TrueMatch history format to M Agent format.
        Ensures proper role and content structure.

        Args:
            history: List of {role, content, ...} dicts from chat

        Returns:
            List of {role, content} dicts for M Agent
        """
        prepared = []
        for turn in history:
            if "role" in turn and "content" in turn:
                prepared.append({
                    "role": turn["role"],
                    "content": turn["content"],
                })

        self.logger.debug(f"[M Agent] Prepared {len(prepared)} history turns")
        return prepared

    def _convert_actions(
        self,
        pending_actions: list[dict],
        user_id: UUID
    ) -> list[dict]:
        """Convert M Agent pending actions to TrueMatch format.

        M Agent returns tool calls with metadata.
        Convert to standard TrueMatch action format for UI display.

        Args:
            pending_actions: List of actions from M Agent
            user_id: User ID for logging

        Returns:
            List of ActionDetail dicts compatible with TrueMatch UI
        """
        actions = []

        for action in pending_actions:
            converted = {
                "id": action.get("tool_use_id", action.get("id", f"action_{len(actions)}")),
                "description": f"Tool: {action.get('tool_name', 'unknown')}",
                "status": action.get("status", "pending"),
                "type": action.get("tool_name"),
                "requires_confirmation": action.get("status") == "pending_confirmation",
                "tool_input": action.get("tool_input", {}),
            }
            actions.append(converted)

        self.logger.debug(
            f"[M Agent] Converted {len(actions)} actions",
            extra={"user_id": str(user_id)}
        )

        return actions

    def _extract_suggestions(
        self,
        response_text: str,
        pending_actions: list[dict]
    ) -> list[str]:
        """Extract follow-up suggestions from M Agent response.

        Analyzes the response to suggest next actions:
        - If integrity issues found: suggest reference checks
        - If gaps detected: suggest clarification questions
        - If assessment review: suggest comparison with others

        Args:
            response_text: M Agent response text
            pending_actions: Actions taken by M Agent

        Returns:
            List of suggested next steps for UI
        """
        suggestions = []

        # Look for keywords indicating risk/findings
        response_lower = response_text.lower()

        # Risk indicators
        if any(word in response_lower for word in ["high risk", "critical", "concerning"]):
            suggestions.append("Request reference checks")
            suggestions.append("Schedule follow-up interview")

        if any(word in response_lower for word in ["timeline", "gap", "inconsistent"]):
            suggestions.append("Investigate anomalies")
            suggestions.append("Ask candidate directly")

        if any(word in response_lower for word in ["compare", "candidate"]):
            suggestions.append("View side-by-side comparison")
            suggestions.append("Export assessment report")

        # Action-based suggestions
        if pending_actions:
            tool_types = {action.get("tool_name") for action in pending_actions}

            if "check_integrity" in tool_types:
                suggestions.append("Review integrity findings")

            if "get_assessment" in tool_types:
                suggestions.append("See full assessment details")

            if "compare_candidates" in tool_types:
                suggestions.append("Add more candidates to compare")

        # Always offer option to continue conversation
        if not suggestions:
            suggestions.append("Ask a follow-up question")

        # Limit to 3 most relevant
        suggestions = suggestions[:3]

        self.logger.debug(
            f"[M Agent] Extracted {len(suggestions)} suggestions"
        )

        return suggestions

    async def _log_learning_data(
        self,
        user_id: UUID,
        session_id: UUID,
        message: str,
        response: str,
        actions: list[dict],
        suggestions: list[str],
        execution_time_ms: int,
        db: AsyncSession,
    ) -> None:
        """Log execution data for agent learning and improvement.

        This captures:
        - Query patterns (intent, keywords, complexity)
        - Response quality signals (user continuation, action usage)
        - Tool effectiveness (which tools were used, returned data quality)
        - Performance metrics (latency, token counts)

        Data can later be used to:
        - Fine-tune system prompts
        - Improve intent classification
        - Optimize tool selection
        - Identify missing tools
        - Personalize to user/role preferences

        Args:
            user_id: User making query
            session_id: Chat session
            message: Original message
            response: M Agent response
            actions: Tools executed
            suggestions: Suggestions provided
            execution_time_ms: Execution time
            db: Database session
        """
        try:
            from app.models.agent_learning import AgentLearningLog

            # Create learning log entry
            learning_log = AgentLearningLog(
                user_id=user_id,
                session_id=session_id,
                agent_type="m_agent_recruiter",
                message_text=message[:1000],  # Store preview
                message_length=len(message),
                response_text=response[:2000],  # Store preview
                response_length=len(response),
                tools_used=[a.get("type") for a in actions],
                tool_count=len(actions),
                suggestions_offered=suggestions,
                execution_time_ms=execution_time_ms,
                created_at=utcnow(),
            )

            db.add(learning_log)
            await db.commit()

            self.logger.debug(
                f"[M Agent] Learning data logged",
                extra={
                    "user_id": str(user_id),
                    "session_id": str(session_id),
                }
            )

        except Exception as e:
            # Don't fail main response if learning log fails
            self.logger.warning(
                f"[M Agent] Failed to log learning data: {str(e)[:100]}"
            )

    async def get_agent_stats(self, user_id: UUID, db: AsyncSession) -> dict:
        """Get M Agent statistics for a user.

        Returns execution stats that can inform personalization.

        Args:
            user_id: User to get stats for
            db: Database session

        Returns:
            Dict with usage stats
        """
        try:
            from app.models.agent_learning import AgentLearningLog
            from sqlalchemy import select, func

            # Query learning logs
            result = await db.execute(
                select(
                    func.count(AgentLearningLog.id).label("total_messages"),
                    func.avg(AgentLearningLog.execution_time_ms).label("avg_latency_ms"),
                    func.avg(AgentLearningLog.tool_count).label("avg_tools_used"),
                )
                .where(AgentLearningLog.user_id == user_id)
                .where(AgentLearningLog.agent_type == "m_agent_recruiter")
            )

            row = result.scalar_one_or_none()

            if row:
                return {
                    "total_messages": row.total_messages,
                    "avg_latency_ms": float(row.avg_latency_ms or 0),
                    "avg_tools_used": float(row.avg_tools_used or 0),
                }
            else:
                return {
                    "total_messages": 0,
                    "avg_latency_ms": 0,
                    "avg_tools_used": 0,
                }

        except Exception as e:
            self.logger.warning(f"[M Agent] Failed to get stats: {str(e)[:100]}")
            return {}
