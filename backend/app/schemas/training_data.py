"""
Pydantic schemas for training data endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─ Upload Request/Response ──────────────────────────────────────────────────


class TrainingDataItemSchema(BaseModel):
    """Individual training data item."""

    id: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    decision: str  # hire, reject, applied, interested, not_interested
    reasoning: Optional[str] = None
    rating: Optional[int] = None
    extracted_capabilities: list[str]
    extracted_credentials: list[str]
    capability_confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingDataUploadSchema(BaseModel):
    """Training data upload response."""

    id: str
    filename: str
    format: str  # csv, json
    row_count: int
    status: str  # pending, processing, completed, failed
    items_processed: int
    items_failed: int
    insights_extracted: int
    processing_stats: dict
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingDataUploadDetailSchema(TrainingDataUploadSchema):
    """Detailed upload with items."""

    items: list[TrainingDataItemSchema] = []


class UploadResultSchema(BaseModel):
    """Results from processing an upload."""

    upload_id: str
    items_processed: int
    items_failed: int
    insights_extracted: int
    new_capabilities: list[str]
    updated_mappings: list[dict]
    improvement_delta: dict  # { metric: change }
    processing_time_seconds: float


# ─ Chat Request/Response ────────────────────────────────────────────────────


class TrainingChatMessageSchema(BaseModel):
    """Training chat message."""

    id: str
    user_message: str
    ai_response: str
    feedback_type: Optional[str] = None
    extracted_training_signal: Optional[dict] = None
    applied_to_training: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingChatRequestSchema(BaseModel):
    """Training chat request."""

    session_id: str
    message: str = Field(..., min_length=1, max_length=2000)


class TrainingChatResponseSchema(BaseModel):
    """Training chat response."""

    message_id: str
    ai_response: str
    feedback_type: Optional[str] = None
    extracted_training_signal: Optional[dict] = None
    applied_changes: Optional[dict] = None
    learning_impact: Optional[dict] = None


class TrainingChatHistorySchema(BaseModel):
    """Chat history response."""

    session_id: str
    messages: list[TrainingChatMessageSchema]
    total_insights: int
    total_updates: int
    created_at: datetime


# ─ Learning Status/Metrics ──────────────────────────────────────────────────


class LearningMetricsSchema(BaseModel):
    """Learning progress metrics."""

    total_feedback_samples: int
    total_insights_extracted: int
    capability_mappings_learned: int
    credential_equivalencies_discovered: int
    success_patterns_identified: int

    # Improvement metrics
    match_accuracy_improvement: float
    hire_success_improvement: float
    capability_coverage_improvement: float

    # Timeline
    last_learning_at: datetime
    learning_velocity: float  # insights per day

    class Config:
        from_attributes = True


class LearningStatusSchema(BaseModel):
    """Current learning system status."""

    is_learning: bool
    active_uploads: int
    active_chat_sessions: int
    pending_items: int
    last_improvement: Optional[dict] = None
    next_auto_learn_at: Optional[datetime] = None
    learning_metrics: LearningMetricsSchema


class ImprovementMetricsSchema(BaseModel):
    """Detailed improvement metrics."""

    timestamp: datetime
    metric_name: str
    baseline_value: float
    current_value: float
    improvement_percent: float
    source: str  # upload, chat, auto
    sample_size: int
    description: str


# ─ Insight Batch Response ───────────────────────────────────────────────────


class TrainingInsightBatchSchema(BaseModel):
    """Results from learning batch."""

    id: str
    source: str  # upload, chat, auto
    insights: list[str]
    new_capabilities: list[str]
    updated_mappings: list[dict]
    updated_credentials: list[dict]
    new_success_patterns: list[dict]
    improvement_metrics: dict
    match_accuracy_delta: float
    hire_success_delta: float
    created_at: datetime
    applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─ Session Management ───────────────────────────────────────────────────────


class TrainingLearningSessionSchema(BaseModel):
    """Training learning session."""

    id: str
    title: Optional[str] = None
    message_count: int
    insights_extracted: int
    mappings_updated: int
    patterns_discovered: int
    status: str  # active, archived
    created_at: datetime
    last_message_at: Optional[datetime] = None


class CreateSessionRequestSchema(BaseModel):
    """Create new learning session."""

    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


# ─ Bulk Upload Processing ───────────────────────────────────────────────────


class BulkTrainingDataSchema(BaseModel):
    """Bulk training data for upload (CSV/JSON parsed)."""

    items: list[dict]
    metadata: Optional[dict] = None


class TrainingDataValidationSchema(BaseModel):
    """Validation results for training data."""

    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[dict]
    preview: list[dict]  # First 5 rows
    estimated_insights: int
