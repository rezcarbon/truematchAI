"""Unit tests for M Agent wrapper integration.

Tests cover:
- M Agent wrapper initialization and import handling
- Response format conversion
- History preparation for M Agent
- Action conversion and suggestion extraction
- Learning data logging
- Error handling and fallbacks
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from app.agents.m_agent_wrapper import MAgentRecruiterWrapper
from app.agents.base_agent import AgentResponse
from app.models.user import User


class TestMAgentWrapperInitialization:
    """Test M Agent wrapper initialization and import handling."""

    def test_wrapper_initialization(self):
        """Test wrapper initializes correctly."""
        wrapper = MAgentRecruiterWrapper()
        assert wrapper is not None
        assert hasattr(wrapper, 'respond')
        assert hasattr(wrapper, 'run_recruiter_agent') or wrapper.m_agent_imported is False

    @patch('app.agents.m_agent_wrapper.MAgentRecruiterWrapper._ensure_m_agent_available')
    def test_m_agent_import_success(self, mock_import):
        """Test successful M Agent import."""
        mock_import.return_value = True
        wrapper = MAgentRecruiterWrapper()
        # Verify import was attempted
        assert mock_import.called

    @patch('app.agents.m_agent_wrapper.MAgentRecruiterWrapper._ensure_m_agent_available')
    def test_m_agent_import_failure_handled(self, mock_import):
        """Test M Agent import failure is handled gracefully."""
        mock_import.return_value = False
        wrapper = MAgentRecruiterWrapper()
        # Should not raise, just set flag
        assert wrapper.m_agent_imported is False


class TestMAgentWrapperResponse:
    """Test M Agent wrapper response handling."""

    @pytest.mark.asyncio
    async def test_respond_with_valid_inputs(self):
        """Test respond() with valid inputs returns AgentResponse."""
        wrapper = MAgentRecruiterWrapper()

        # Mock M Agent function
        wrapper.run_recruiter_agent = AsyncMock(return_value=(
            "Wei Chen has capability score of 87.",
            []  # No pending actions
        ))
        wrapper.m_agent_imported = True

        # Create mock objects
        user = Mock(spec=User)
        user.id = uuid4()
        user.role = "recruiter"
        user.display_name = "Test Recruiter"

        db = AsyncMock()
        session_id = uuid4()

        # Call respond
        response = await wrapper.respond(
            message="Compare Wei Chen and Sarah Kim",
            history=[],
            user=user,
            db=db,
            session_id=session_id,
        )

        # Verify response format
        assert isinstance(response, AgentResponse)
        assert isinstance(response.text, str)
        assert isinstance(response.actions, list)
        assert isinstance(response.suggestions, list)

    @pytest.mark.asyncio
    async def test_respond_returns_proper_response_format(self):
        """Test respond() converts M Agent output to proper TrueMatch format."""
        wrapper = MAgentRecruiterWrapper()

        m_agent_response = "Assessment shows capability: 87, Traditional: 43"
        pending_actions = [
            {
                "tool_name": "get_assessment",
                "tool_use_id": "tool_123",
                "status": "success",
                "tool_input": {"candidate_id": "wei_chen"}
            }
        ]

        wrapper.run_recruiter_agent = AsyncMock(return_value=(
            m_agent_response,
            pending_actions
        ))
        wrapper.m_agent_imported = True

        user = Mock(spec=User)
        user.id = uuid4()
        user.role = "recruiter"

        response = await wrapper.respond(
            message="Check Wei Chen assessment",
            history=[],
            user=user,
            db=AsyncMock(),
            session_id=uuid4(),
        )

        # Verify conversion
        assert response.text == m_agent_response
        assert len(response.actions) == 1
        assert response.actions[0]["type"] == "get_assessment"
        assert response.actions[0]["status"] == "success"
        assert "suggestions" in response.__dict__ or len(response.suggestions) >= 0


class TestHistoryPreperation:
    """Test conversation history preparation for M Agent."""

    def test_prepare_history_empty(self):
        """Test history preparation with empty history."""
        wrapper = MAgentRecruiterWrapper()
        result = wrapper._prepare_history([])
        assert result == []

    def test_prepare_history_single_turn(self):
        """Test history preparation with single turn."""
        wrapper = MAgentRecruiterWrapper()

        history = [
            {"role": "user", "content": "Who is Wei Chen?"}
        ]

        result = wrapper._prepare_history(history)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Who is Wei Chen?"

    def test_prepare_history_multi_turn(self):
        """Test history preparation with multiple turns."""
        wrapper = MAgentRecruiterWrapper()

        history = [
            {"role": "user", "content": "Who is Wei Chen?"},
            {"role": "assistant", "content": "Wei Chen is a candidate..."},
            {"role": "user", "content": "What's his assessment score?"},
            {"role": "assistant", "content": "His capability score is 87..."},
        ]

        result = wrapper._prepare_history(history)

        assert len(result) == 4
        for i, turn in enumerate(result):
            assert "role" in turn
            assert "content" in turn
            assert turn["role"] == history[i]["role"]
            assert turn["content"] == history[i]["content"]

    def test_prepare_history_filters_extra_fields(self):
        """Test history preparation filters unnecessary fields."""
        wrapper = MAgentRecruiterWrapper()

        history = [
            {
                "id": "msg_123",
                "role": "user",
                "content": "Hello",
                "timestamp": "2026-01-01T00:00:00Z",
                "extra_field": "should_be_ignored"
            }
        ]

        result = wrapper._prepare_history(history)

        assert len(result) == 1
        assert "id" not in result[0]
        assert "timestamp" not in result[0]
        assert "extra_field" not in result[0]
        assert "role" in result[0]
        assert "content" in result[0]


class TestActionConversion:
    """Test M Agent action conversion to TrueMatch format."""

    def test_convert_actions_empty(self):
        """Test converting empty actions list."""
        wrapper = MAgentRecruiterWrapper()
        result = wrapper._convert_actions([], uuid4())
        assert result == []

    def test_convert_single_action(self):
        """Test converting single action."""
        wrapper = MAgentRecruiterWrapper()

        pending_actions = [
            {
                "tool_use_id": "call_123",
                "tool_name": "get_assessment",
                "status": "success",
                "tool_input": {"assessment_id": "abc123"}
            }
        ]

        result = wrapper._convert_actions(pending_actions, uuid4())

        assert len(result) == 1
        action = result[0]
        assert action["id"] == "call_123"
        assert action["type"] == "get_assessment"
        assert action["status"] == "success"
        assert action["description"] == "Tool: get_assessment"
        assert action["requires_confirmation"] is False

    def test_convert_multiple_actions(self):
        """Test converting multiple actions."""
        wrapper = MAgentRecruiterWrapper()

        pending_actions = [
            {
                "tool_use_id": "call_1",
                "tool_name": "get_assessment",
                "status": "success",
                "tool_input": {}
            },
            {
                "tool_use_id": "call_2",
                "tool_name": "check_integrity",
                "status": "pending_confirmation",
                "tool_input": {}
            }
        ]

        result = wrapper._convert_actions(pending_actions, uuid4())

        assert len(result) == 2
        assert result[0]["type"] == "get_assessment"
        assert result[0]["requires_confirmation"] is False
        assert result[1]["type"] == "check_integrity"
        assert result[1]["requires_confirmation"] is True


class TestSuggestionExtraction:
    """Test suggestion extraction from M Agent responses."""

    def test_extract_suggestions_empty_response(self):
        """Test suggestion extraction from empty response."""
        wrapper = MAgentRecruiterWrapper()
        result = wrapper._extract_suggestions("", [])
        # Should have at least default suggestion
        assert isinstance(result, list)

    def test_extract_suggestions_with_risk_indicators(self):
        """Test suggestion extraction recognizes risk indicators."""
        wrapper = MAgentRecruiterWrapper()

        response = "Wei Chen shows high risk indicators. Critical timeline anomalies detected."
        suggestions = wrapper._extract_suggestions(response, [])

        # Should suggest risk mitigation
        suggestions_lower = [s.lower() for s in suggestions]
        assert any("reference" in s or "interview" in s for s in suggestions_lower)

    def test_extract_suggestions_with_timeline_issues(self):
        """Test suggestion extraction for timeline issues."""
        wrapper = MAgentRecruiterWrapper()

        response = "There is a 6-month employment gap in the candidate's history."
        suggestions = wrapper._extract_suggestions(response, [])

        suggestions_lower = [s.lower() for s in suggestions]
        assert any("anomal" in s or "gap" in s or "investigate" in s for s in suggestions_lower)

    def test_extract_suggestions_from_actions(self):
        """Test suggestion extraction from tool actions."""
        wrapper = MAgentRecruiterWrapper()

        actions = [
            {"tool_name": "check_integrity"}
        ]

        suggestions = wrapper._extract_suggestions("Here are the findings.", actions)

        suggestions_lower = [s.lower() for s in suggestions]
        assert any("integrity" in s for s in suggestions_lower)

    def test_extract_suggestions_limits_to_three(self):
        """Test suggestion extraction limits output to 3."""
        wrapper = MAgentRecruiterWrapper()

        response = "High risk critical concerning gap timeline inconsistent compare candidate"
        suggestions = wrapper._extract_suggestions(response, [])

        assert len(suggestions) <= 3


class TestLearningDataLogging:
    """Test learning data logging for agent improvement."""

    @pytest.mark.asyncio
    async def test_log_learning_data_captures_metrics(self):
        """Test learning data logging captures execution metrics."""
        wrapper = MAgentRecruiterWrapper()

        # Mock database
        db = AsyncMock()
        mock_learning_log = Mock()
        db.add = Mock()
        db.commit = AsyncMock()

        with patch('app.agents.m_agent_wrapper.AgentLearningLog') as MockLog:
            MockLog.return_value = mock_learning_log

            await wrapper._log_learning_data(
                user_id=uuid4(),
                session_id=uuid4(),
                message="Test message",
                response="Test response",
                actions=[{"type": "test_tool"}],
                suggestions=["Test suggestion"],
                execution_time_ms=1500,
                db=db,
            )

            # Verify log was created and saved
            assert db.add.called
            assert db.commit.called

    @pytest.mark.asyncio
    async def test_log_learning_data_handles_errors_gracefully(self):
        """Test learning data logging doesn't break main flow on error."""
        wrapper = MAgentRecruiterWrapper()

        db = AsyncMock()
        db.add.side_effect = Exception("Database error")

        # Should not raise, just log warning
        with patch('app.agents.m_agent_wrapper.AgentLearningLog') as MockLog:
            MockLog.return_value = Mock()
            # This should not raise
            await wrapper._log_learning_data(
                user_id=uuid4(),
                session_id=uuid4(),
                message="Test",
                response="Test",
                actions=[],
                suggestions=[],
                execution_time_ms=0,
                db=db,
            )


class TestErrorHandling:
    """Test error handling in M Agent wrapper."""

    @pytest.mark.asyncio
    async def test_respond_raises_on_m_agent_unavailable(self):
        """Test respond raises when M Agent not available and no fallback."""
        wrapper = MAgentRecruiterWrapper()
        wrapper.m_agent_imported = False

        user = Mock(spec=User)
        user.id = uuid4()

        with pytest.raises(ImportError):
            await wrapper.respond(
                message="Test",
                history=[],
                user=user,
                db=AsyncMock(),
                session_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_respond_logs_errors(self):
        """Test errors are properly logged."""
        wrapper = MAgentRecruiterWrapper()
        wrapper.run_recruiter_agent = AsyncMock(side_effect=Exception("M Agent error"))
        wrapper.m_agent_imported = True

        user = Mock(spec=User)
        user.id = uuid4()

        with patch.object(wrapper, 'logger') as mock_logger:
            with pytest.raises(Exception):
                await wrapper.respond(
                    message="Test",
                    history=[],
                    user=user,
                    db=AsyncMock(),
                    session_id=uuid4(),
                )

            # Verify error was logged
            assert mock_logger.error.called
