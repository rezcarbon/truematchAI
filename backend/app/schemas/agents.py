"""Schemas for agent control & monitoring API.

Extends the queue item models with decision support fields and agent health metrics.
"""
from __future__ import annotations

from datetime import datetime
from app.core.clock import utcnow
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class QueueItemDetail(BaseModel):
    """Full details of an ingest queue item with decision support fields."""

    # Core identity
    id: UUID
    source: str
    ingest_type: str
    status: str
    created_at: str

    # Related resources
    resume_id: Optional[UUID] = None
    assessment_id: Optional[UUID] = None
    position_id: Optional[UUID] = None

    # Processing state
    retry_count: int
    source_ref: Optional[str] = None
    last_error: Optional[str] = None

    # JD analysis
    jd_agent_output: Optional[dict] = None

    # Decision support fields
    awaiting_review: bool = Field(
        default=False,
        description="True if item is in awaiting_review status"
    )
    decision_deadline: Optional[datetime] = Field(
        default=None,
        description="Optional deadline for human review decision"
    )
    notes_history: list[str] = Field(
        default_factory=list,
        description="Chronological history of review notes"
    )
    sender_name: Optional[str] = Field(
        default=None,
        description="Name of sender/submitter (from sender_meta)"
    )
    review_notes: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Health and activity status for an agent (CV, JD, or Email)."""

    agent_type: str = Field(
        description="Type of agent: 'cv', 'jd', or 'email'"
    )
    running: bool = Field(
        description="Whether the agent has active workers"
    )
    queue_size: int = Field(
        ge=0,
        description="Number of items awaiting processing"
    )
    processed_24h: int = Field(
        ge=0,
        description="Items successfully processed in last 24 hours"
    )
    failed_24h: int = Field(
        ge=0,
        description="Items that failed in last 24 hours"
    )
    avg_processing_time_seconds: Optional[float] = Field(
        default=None,
        description="Average time to process items (in seconds)"
    )
    last_activity_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last successful processing"
    )


class AgentsStatusResponse(BaseModel):
    """Overall agent system health dashboard."""

    cv: AgentStatusResponse
    jd: AgentStatusResponse
    email: AgentStatusResponse
    timestamp: datetime = Field(
        default_factory=utcnow,
        description="Timestamp of this status snapshot"
    )


class AgentMetricsResponse(BaseModel):
    """Detailed throughput and error metrics for a specific agent."""

    agent_type: str
    period_hours: int = Field(
        description="Metrics period in hours (e.g., 24, 7*24)"
    )
    total_processed: int
    total_failed: int
    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of items successfully processed"
    )
    avg_processing_time_seconds: float
    p50_processing_time_seconds: float
    p95_processing_time_seconds: float
    p99_processing_time_seconds: float
    error_breakdown: dict[str, int] = Field(
        description="Count of failures by error type"
    )
    throughput_per_hour: float = Field(
        description="Average items processed per hour"
    )


class QueueItemAction(BaseModel):
    """Event payload for queue item state changes."""

    event: str = Field(
        description="Action event: 'approved', 'rejected', 'reassigned'"
    )
    item_id: UUID
    item_status: str
    action_by_user_id: UUID
    action_notes: Optional[str] = None
    assessment_id: Optional[UUID] = None
    target_position_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=utcnow)


class WebSocketEventMessage(BaseModel):
    """Generic WebSocket event message."""

    type: str = Field(description="Event type for routing")
    timestamp: datetime = Field(default_factory=utcnow)
    data: dict = Field(default_factory=dict, description="Event-specific payload")
