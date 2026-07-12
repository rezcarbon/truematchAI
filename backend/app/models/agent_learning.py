"""Agent Learning Log model for capturing agent execution data.

This model stores execution telemetry for:
- Agent behavior analysis
- Learning signal collection
- Performance monitoring
- User personalization
- Continuous improvement

Each log entry captures:
- Query characteristics (length, complexity, intent)
- Response quality (effectiveness, relevance)
- Tool usage patterns (which tools, how often)
- Execution performance (latency, token usage)
- User engagement signals

Over time, this data enables:
1. Prompt optimization (understanding what works)
2. Tool enhancement (which tools are most valuable)
3. Intent detection improvement (pattern recognition)
4. User personalization (preferences per recruiter)
5. Anomaly detection (unusual query patterns)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class AgentLearningLog(Base):
    """Learning log for agent execution tracking.

    Captures telemetry about agent behavior, tool usage, and performance
    for analysis and continuous improvement.
    """

    __tablename__ = "agent_learning_logs"

    # Primary key and relationships
    id = Column(PGUUID, primary_key=True, default=UUID)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(PGUUID, ForeignKey("chat_sessions.id"), nullable=True, index=True)

    # Agent metadata
    agent_type = Column(String(50), nullable=False, default="m_agent_recruiter")  # m_agent_recruiter, m_agent_admin, local_agent, etc.

    # Query characteristics (for understanding input patterns)
    message_text = Column(Text, nullable=False)  # Original user message (first 1000 chars)
    message_length = Column(Integer, nullable=False)  # Full message length
    message_keywords = Column(ARRAY(String), nullable=True)  # Extracted keywords for quick analysis

    # Response characteristics (for quality assessment)
    response_text = Column(Text, nullable=False)  # Agent response (first 2000 chars)
    response_length = Column(Integer, nullable=False)  # Full response length

    # Tool usage (for understanding agent behavior)
    tools_used = Column(ARRAY(String), nullable=True)  # List of tool names executed
    tool_count = Column(Integer, nullable=False, default=0)  # How many tools were used
    tool_execution_times = Column(JSON, nullable=True)  # {tool_name: ms} dict

    # Suggestions (for understanding next-step effectiveness)
    suggestions_offered = Column(ARRAY(String), nullable=True)  # Suggestions shown to user
    suggestion_clicked = Column(String, nullable=True)  # Which suggestion (if any) user clicked

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=False)  # Total query latency
    token_count = Column(Integer, nullable=True)  # LLM tokens used
    token_cost_usd = Column(Float, nullable=True)  # Estimated cost

    # Quality signals (collected from user behavior)
    user_rating = Column(Integer, nullable=True)  # 1-5 rating if user provided
    user_continued_conversation = Column(Integer, nullable=True)  # 1 if user sent follow-up, 0 otherwise
    user_took_suggested_action = Column(Integer, nullable=True)  # 1 if user clicked suggestion
    followup_action_type = Column(String(100), nullable=True)  # What action user took (e.g., "viewed_assessment")

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata for debugging/analysis
    metadata = Column(JSON, nullable=True)  # Additional context as needed

    def __repr__(self) -> str:
        return f"AgentLearningLog(user_id={self.user_id}, agent={self.agent_type}, tools={self.tool_count})"


class AgentImprovement(Base):
    """Record of agent improvements based on learning data.

    Tracks changes made to agents (prompt updates, tool additions, etc.)
    and their impact on performance metrics.
    """

    __tablename__ = "agent_improvements"

    # Primary key
    id = Column(PGUUID, primary_key=True, default=UUID)

    # What was changed
    agent_type = Column(String(50), nullable=False)  # m_agent_recruiter, etc.
    improvement_type = Column(String(50), nullable=False)  # prompt_update, tool_added, intent_model_retrained, etc.
    description = Column(Text, nullable=False)  # What changed and why
    implementation_details = Column(JSON, nullable=True)  # Code changes, new parameters, etc.

    # Impact metrics
    avg_response_latency_before_ms = Column(Integer, nullable=True)
    avg_response_latency_after_ms = Column(Integer, nullable=True)
    user_satisfaction_before = Column(Float, nullable=True)  # Average rating before
    user_satisfaction_after = Column(Float, nullable=True)  # Average rating after
    tool_usage_change = Column(JSON, nullable=True)  # {tool: change_percent} dict
    token_cost_change_percent = Column(Float, nullable=True)  # % increase/decrease

    # Timing
    deployed_at = Column(DateTime, nullable=False)
    evaluation_period_days = Column(Integer, nullable=True)  # How long it was evaluated for
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Rollback info
    is_active = Column(Integer, nullable=False, default=1)  # 1 if active, 0 if rolled back
    rolled_back_at = Column(DateTime, nullable=True)  # When rolled back (if applicable)
    rollback_reason = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"AgentImprovement(agent={self.agent_type}, type={self.improvement_type}, active={self.is_active})"
