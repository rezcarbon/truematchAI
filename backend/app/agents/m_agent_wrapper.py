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
from app.agents.recruiter_agent import RecruiterAgent
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
        """Initialize the M Agent wrapper with fallback support.

        Creates both M Agent and a fallback local RecruiterAgent.
        If M Agent is unavailable, requests are automatically routed to the fallback.
        """
        self.logger = logging.getLogger(__name__)
        self.m_agent_imported = False
        self.fallback_agent = RecruiterAgent()
        self.logger.info("[M Agent] Fallback agent (RecruiterAgent) initialized")
        self._ensure_m_agent_available()

    def _ensure_m_agent_available(self) -> bool:
        """Verify M Agent is importable from m-agent-hackathon.

        If available, M Agent will be used for recruiter queries with advanced
        capabilities (intent classification, agentic loop, integrity analysis).
        If unavailable, fallback to local RecruiterAgent.

        Returns:
            True if M Agent available, False otherwise (fallback mode)
        """
        try:
            # Try importing M Agent components
            from m_agent_hackathon.backend.app.agents.m_agent_recruiter import (
                run_recruiter_agent
            )
            self.run_recruiter_agent = run_recruiter_agent
            self.m_agent_imported = True
            self.logger.info("[M Agent] ✅ Import successful - M Agent Layer 1 & 2 active")
            return True
        except ImportError as e:
            self.logger.error(f"[M Agent] ❌ Import failed: {e}")
            self.logger.warning(
                "[M Agent] ⚠️  M Agent package unavailable - "
                "falling back to local RecruiterAgent for full service continuity"
            )
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
                # FALLBACK: M Agent not available, use local RecruiterAgent
                self.logger.warning(
                    "[M Agent] ⚠️  M Agent not available - routing to fallback agent",
                    extra=execution_context
                )
                self.logger.info(
                    "[M Agent] 🔄 Fallback: Routing to local RecruiterAgent",
                    extra=execution_context
                )
                # Delegate to fallback agent - same interface, full compatibility
                fallback_response = await self.fallback_agent.respond(
                    message=message,
                    history=history,
                    user=user,
                    db=db,
                    session_id=session_id,
                    mode=mode,
                    candidate_context=candidate_context,
                    stream_callback=stream_callback,
                )
                # Add metadata to indicate fallback was used
                fallback_response.metadata = {
                    "agent": "fallback_recruiter_agent",
                    "m_agent_available": False,
                    "fallback_active": True,
                    "streaming_supported": True,
                }
                self.logger.info(
                    "[M Agent] ✅ Fallback completed successfully",
                    extra={
                        **execution_context,
                        "response_length": len(fallback_response.text),
                        "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    }
                )
                return fallback_response

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
            # Log error but don't re-raise - attempt fallback on any M Agent error
            error_msg = str(e)[:200]
            self.logger.error(
                f"[M Agent] ❌ Error in M Agent path: {error_msg}",
                extra=execution_context,
                exc_info=True
            )

            # If M Agent path failed, try fallback agent as last resort
            try:
                self.logger.warning(
                    "[M Agent] 🔄 Attempting fallback to local RecruiterAgent due to M Agent error",
                    extra=execution_context
                )
                fallback_response = await self.fallback_agent.respond(
                    message=message,
                    history=history,
                    user=user,
                    db=db,
                    session_id=session_id,
                    mode=mode,
                    candidate_context=candidate_context,
                    stream_callback=stream_callback,
                )
                # Mark response as fallback recovery
                fallback_response.metadata = {
                    "agent": "fallback_recruiter_agent",
                    "m_agent_error_recovery": True,
                    "fallback_active": True,
                    "original_error": error_msg,
                    "streaming_supported": True,
                }
                self.logger.info(
                    "[M Agent] ✅ Fallback recovered from M Agent error",
                    extra=execution_context
                )
                return fallback_response
            except Exception as fallback_error:
                # Both M Agent and fallback failed - this is critical
                self.logger.critical(
                    f"[M Agent] 🔴 CRITICAL: Both M Agent and fallback failed. "
                    f"M Agent error: {error_msg}. Fallback error: {str(fallback_error)[:200]}",
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
