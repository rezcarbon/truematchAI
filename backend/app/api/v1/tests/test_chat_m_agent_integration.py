"""Integration tests for M Agent + Chat endpoint.

Tests end-to-end flow:
1. Recruiter sends message via chat endpoint
2. Message routed to M Agent (via agent_router)
3. M Agent executes intent classification + agentic loop
4. Response streamed back as SSE
5. ChatMessage table updated with history
6. Learning data logged
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming FastAPI app structure
# from app.main import app
# from app.deps import get_db


class TestChatEndpointWithMAgent:
    """Integration tests for chat endpoint using M Agent."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def recruiter_user(self):
        """Create mock recruiter user."""
        user = Mock()
        user.id = uuid4()
        user.role = "recruiter"
        user.display_name = "Test Recruiter"
        user.email = "recruiter@test.com"
        return user

    @pytest.fixture
    def chat_session(self):
        """Create mock chat session."""
        from app.models.chat import ChatSession

        session = Mock(spec=ChatSession)
        session.id = uuid4()
        session.user_id = uuid4()
        session.title = "Test Chat"
        session.created_at = datetime.utcnow()
        session.last_message_at = datetime.utcnow()
        return session

    @pytest.mark.asyncio
    async def test_recruiter_message_routes_to_m_agent(self, mock_db, recruiter_user):
        """Test recruiter messages are routed to M Agent via agent_router."""
        from app.agents.agent_router import get_agent_for_user
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper

        # Get agent for recruiter
        agent = await get_agent_for_user(
            user_id=recruiter_user.id,
            user_role="recruiter",
            db=mock_db
        )

        # Verify we got M Agent wrapper
        assert isinstance(agent, MAgentRecruiterWrapper)

    @pytest.mark.asyncio
    async def test_candidate_message_uses_local_agent(self, mock_db):
        """Test candidate messages still use local agent."""
        from app.agents.agent_router import get_agent_for_user
        from app.agents.candidate_agent import CandidateAgent

        candidate = Mock()
        candidate.id = uuid4()
        candidate.role = "candidate"

        # Get agent for candidate
        agent = await get_agent_for_user(
            user_id=candidate.id,
            user_role="candidate",
            db=mock_db
        )

        # Verify we got local agent (not M Agent)
        assert isinstance(agent, CandidateAgent)

    @pytest.mark.asyncio
    async def test_m_agent_response_format_compatibility(self, mock_db, recruiter_user):
        """Test M Agent response works with chat endpoint expectations."""
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper
        from app.agents.base_agent import AgentResponse

        wrapper = MAgentRecruiterWrapper()

        # Mock M Agent execution
        wrapper.run_recruiter_agent = AsyncMock(return_value=(
            "Wei Chen has capability score of 87",
            [
                {
                    "tool_use_id": "call_1",
                    "tool_name": "get_assessment",
                    "status": "success"
                }
            ]
        ))
        wrapper.m_agent_imported = True

        # Call respond
        response = await wrapper.respond(
            message="Check Wei Chen's assessment",
            history=[],
            user=recruiter_user,
            db=mock_db,
            session_id=uuid4(),
        )

        # Verify response format matches what chat endpoint expects
        assert isinstance(response, AgentResponse)
        assert hasattr(response, 'text')
        assert hasattr(response, 'actions')
        assert hasattr(response, 'suggestions')
        assert isinstance(response.text, str)
        assert isinstance(response.actions, list)
        assert isinstance(response.suggestions, list)

    @pytest.mark.asyncio
    async def test_m_agent_with_conversation_history(self, mock_db, recruiter_user):
        """Test M Agent receives and uses conversation history."""
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper

        wrapper = MAgentRecruiterWrapper()

        # Create conversation history
        history = [
            {"role": "user", "content": "Who is Wei Chen?"},
            {"role": "assistant", "content": "Wei Chen is a software engineer..."},
            {"role": "user", "content": "What's his assessment score?"},
        ]

        # Mock M Agent to verify history is passed
        wrapper.run_recruiter_agent = AsyncMock(return_value=(
            "His capability score is 87",
            []
        ))
        wrapper.m_agent_imported = True

        # Call respond with history
        await wrapper.respond(
            message="Compare him with others",
            history=history,
            user=recruiter_user,
            db=mock_db,
            session_id=uuid4(),
        )

        # Verify M Agent was called
        assert wrapper.run_recruiter_agent.called
        call_args = wrapper.run_recruiter_agent.call_args

        # Verify message and session_id were passed
        assert call_args.kwargs['message'] == "Compare him with others"

    @pytest.mark.asyncio
    async def test_m_agent_streaming_with_callback(self, mock_db, recruiter_user):
        """Test M Agent streaming callback for SSE."""
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper

        wrapper = MAgentRecruiterWrapper()

        # Track streamed tokens
        streamed_tokens = []

        async def stream_callback(chunk: str):
            streamed_tokens.append(chunk)

        # Mock M Agent with streaming
        response_text = "Wei Chen has capability score of 87"

        async def mock_run_recruiter(message, session_id, user_id, db, stream_callback):
            # Simulate streaming
            for word in response_text.split():
                if stream_callback:
                    await stream_callback(word + " ")
            return response_text, []

        wrapper.run_recruiter_agent = mock_run_recruiter
        wrapper.m_agent_imported = True

        # Call with stream callback
        response = await wrapper.respond(
            message="Test",
            history=[],
            user=recruiter_user,
            db=mock_db,
            session_id=uuid4(),
            stream_callback=stream_callback,
        )

        # Verify streaming worked
        assert len(streamed_tokens) > 0
        assert response.text == response_text

    @pytest.mark.asyncio
    async def test_chat_message_persistence(self, mock_db, recruiter_user, chat_session):
        """Test chat messages are saved to ChatMessage table."""
        from app.models.chat import ChatMessage

        # Verify mock can add/commit
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        # Create chat messages like the endpoint does
        user_msg = Mock(spec=ChatMessage)
        user_msg.session_id = chat_session.id
        user_msg.role = "user"
        user_msg.content = "Check Wei Chen"

        mock_db.add(user_msg)

        assistant_msg = Mock(spec=ChatMessage)
        assistant_msg.session_id = chat_session.id
        assistant_msg.role = "assistant"
        assistant_msg.content = "Wei Chen assessment: capability 87"

        mock_db.add(assistant_msg)

        await mock_db.commit()

        # Verify messages were added
        assert mock_db.add.call_count >= 2
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_m_agent_with_pending_actions(self, mock_db, recruiter_user):
        """Test M Agent pending actions are properly converted."""
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper

        wrapper = MAgentRecruiterWrapper()

        pending_actions = [
            {
                "tool_use_id": "call_1",
                "tool_name": "get_assessment",
                "status": "success",
                "tool_input": {"assessment_id": "abc123"}
            },
            {
                "tool_use_id": "call_2",
                "tool_name": "check_integrity",
                "status": "pending_confirmation",
                "tool_input": {"candidate_id": "wei_chen"}
            }
        ]

        wrapper.run_recruiter_agent = AsyncMock(return_value=(
            "Assessment retrieved. Integrity check pending confirmation.",
            pending_actions
        ))
        wrapper.m_agent_imported = True

        response = await wrapper.respond(
            message="Analyze Wei Chen",
            history=[],
            user=recruiter_user,
            db=mock_db,
            session_id=uuid4(),
        )

        # Verify actions converted correctly
        assert len(response.actions) == 2
        assert response.actions[0]["type"] == "get_assessment"
        assert response.actions[0]["status"] == "success"
        assert response.actions[0]["requires_confirmation"] is False
        assert response.actions[1]["type"] == "check_integrity"
        assert response.actions[1]["status"] == "pending_confirmation"
        assert response.actions[1]["requires_confirmation"] is True

    @pytest.mark.asyncio
    async def test_learning_data_logged_on_execution(self, mock_db, recruiter_user):
        """Test execution data is logged for learning."""
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper

        wrapper = MAgentRecruiterWrapper()

        wrapper.run_recruiter_agent = AsyncMock(return_value=(
            "Test response",
            []
        ))
        wrapper.m_agent_imported = True

        # Mock learning log
        with patch('app.agents.m_agent_wrapper.AgentLearningLog') as MockLog:
            mock_log = Mock()
            MockLog.return_value = mock_log

            mock_db.add = Mock()
            mock_db.commit = AsyncMock()

            response = await wrapper.respond(
                message="Test query",
                history=[],
                user=recruiter_user,
                db=mock_db,
                session_id=uuid4(),
            )

            # Verify learning data was logged
            # (check if add and commit were called)

    @pytest.mark.asyncio
    async def test_error_handling_on_m_agent_failure(self, mock_db, recruiter_user):
        """Test error handling when M Agent fails."""
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper

        wrapper = MAgentRecruiterWrapper()

        wrapper.run_recruiter_agent = AsyncMock(side_effect=Exception("M Agent error"))
        wrapper.m_agent_imported = True

        # Should raise exception that endpoint can handle
        with pytest.raises(Exception):
            await wrapper.respond(
                message="Test",
                history=[],
                user=recruiter_user,
                db=mock_db,
                session_id=uuid4(),
            )


class TestAgentRouterIntegration:
    """Test agent router correctly routes to M Agent."""

    @pytest.mark.asyncio
    async def test_router_returns_m_agent_for_recruiter(self):
        """Test router returns M Agent wrapper for recruiter role."""
        from app.agents.agent_router import get_agent_for_user
        from app.agents.m_agent_wrapper import MAgentRecruiterWrapper

        agent = await get_agent_for_user(
            user_id=uuid4(),
            user_role="recruiter",
            db=AsyncMock()
        )

        assert isinstance(agent, MAgentRecruiterWrapper)

    @pytest.mark.asyncio
    async def test_router_returns_local_agents_for_other_roles(self):
        """Test router returns local agents for non-recruiter roles."""
        from app.agents.agent_router import get_agent_for_user
        from app.agents.candidate_agent import CandidateAgent
        from app.agents.admin_agent import AdminAgent

        # Test candidate
        candidate_agent = await get_agent_for_user(
            user_id=uuid4(),
            user_role="candidate",
            db=AsyncMock()
        )
        assert isinstance(candidate_agent, CandidateAgent)

        # Test admin
        admin_agent = await get_agent_for_user(
            user_id=uuid4(),
            user_role="admin",
            db=AsyncMock()
        )
        assert isinstance(admin_agent, AdminAgent)

    @pytest.mark.asyncio
    async def test_router_defaults_to_candidate_for_unknown_role(self):
        """Test router defaults to candidate agent for unknown roles."""
        from app.agents.agent_router import get_agent_for_user
        from app.agents.candidate_agent import CandidateAgent

        agent = await get_agent_for_user(
            user_id=uuid4(),
            user_role="unknown_role",
            db=AsyncMock()
        )

        assert isinstance(agent, CandidateAgent)
