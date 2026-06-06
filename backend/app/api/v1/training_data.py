"""
Training Data API Endpoints - Upload & Chat for autonomous AI-native training.

Allows admins to:
1. Upload training data (CSV/JSON) with candidate feedback
2. Have chat-based training conversations
3. Track auto-learning progress
"""
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_admin
from app.database import get_session
from app.models.user import User
from app.models.training_data import (
    TrainingDataUpload,
    TrainingDataItem,
    TrainingChatMessage,
    TrainingLearningSession,
)
from app.schemas.training_data import (
    TrainingDataUploadSchema,
    TrainingDataUploadDetailSchema,
    UploadResultSchema,
    TrainingChatRequestSchema,
    TrainingChatResponseSchema,
    TrainingChatHistorySchema,
    TrainingChatMessageSchema,
    LearningStatusSchema,
    LearningMetricsSchema,
    TrainingLearningSessionSchema,
    CreateSessionRequestSchema,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/training/data", tags=["training-data"])


# ─ Upload Endpoints ─────────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=TrainingDataUploadSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload training data (CSV/JSON)",
    description="Upload training feedback data for the virtual brain to learn from. Returns 202 Accepted - processing happens asynchronously.",
)
async def upload_training_data(
    file: UploadFile = File(..., description="CSV or JSON file with training data"),
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> TrainingDataUploadSchema:
    """
    Upload training data file (CSV/JSON).

    CSV format should have columns:
    - candidate_name, candidate_email
    - decision (hire/reject/applied/interested/not_interested)
    - reasoning (text explanation)
    - rating (1-5, optional)
    - skills (comma-separated, optional)

    JSON format should be array of objects with above fields.

    Returns immediately with upload_id. Processing happens asynchronously.
    """
    if file.size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Determine file format
    if file.filename.endswith(".csv"):
        file_format = "csv"
    elif file.filename.endswith(".json"):
        file_format = "json"
    else:
        raise HTTPException(
            status_code=400, detail="File must be CSV or JSON format"
        )

    # Create upload record
    upload = TrainingDataUpload(
        id=uuid4(),
        user_id=admin.id,
        filename=file.filename,
        format=file_format,
        status="pending",
    )

    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    logger.info(
        f"Training data upload started",
        extra={
            "upload_id": upload.id,
            "filename": file.filename,
            "format": file_format,
            "user_id": admin.id,
        },
    )

    # TODO: Queue async job to process file
    # For now, return immediately (processing will happen in background)

    return TrainingDataUploadSchema.from_orm(upload)


@router.get(
    "/uploads",
    response_model=list[TrainingDataUploadSchema],
    summary="List training uploads",
    description="Get list of all training data uploads for the current admin user.",
)
async def list_uploads(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> list[TrainingDataUploadSchema]:
    """Get list of training data uploads."""
    query = (
        select(TrainingDataUpload)
        .where(TrainingDataUpload.user_id == admin.id)
        .order_by(TrainingDataUpload.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    uploads = result.scalars().all()

    return [TrainingDataUploadSchema.from_orm(u) for u in uploads]


@router.get(
    "/upload/{upload_id}",
    response_model=TrainingDataUploadDetailSchema,
    summary="Get upload details",
    description="Get detailed information about a training data upload including all processed items.",
)
async def get_upload_detail(
    upload_id: str,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> TrainingDataUploadDetailSchema:
    """Get detailed upload information."""
    query = select(TrainingDataUpload).where(
        (TrainingDataUpload.id == upload_id) & (TrainingDataUpload.user_id == admin.id)
    )

    result = await db.execute(query)
    upload = result.scalar_one_or_none()

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    return TrainingDataUploadDetailSchema.from_orm(upload)


@router.get(
    "/upload/{upload_id}/status",
    response_model=UploadResultSchema,
    summary="Check upload processing status",
    description="Check the current status and results of a training data upload.",
)
async def get_upload_status(
    upload_id: str,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> UploadResultSchema:
    """Get upload processing status and results."""
    query = select(TrainingDataUpload).where(
        (TrainingDataUpload.id == upload_id) & (TrainingDataUpload.user_id == admin.id)
    )

    result = await db.execute(query)
    upload = result.scalar_one_or_none()

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    return UploadResultSchema(
        upload_id=upload.id,
        items_processed=upload.items_processed,
        items_failed=upload.items_failed,
        insights_extracted=upload.insights_extracted,
        new_capabilities=[],  # TODO: Get from TrainingInsightBatch
        updated_mappings=[],  # TODO: Get from TrainingInsightBatch
        improvement_delta={},  # TODO: Calculate
        processing_time_seconds=0.0,  # TODO: Calculate
    )


# ─ Chat Endpoints ───────────────────────────────────────────────────────────


@router.post(
    "/chat",
    response_model=TrainingChatResponseSchema,
    summary="Send training feedback message",
    description="Send a message to train the system. Chat-based training allows natural feedback like 'This candidate should match Senior Engineer' or 'Improve your matching for Python skills'.",
)
async def send_training_message(
    request: TrainingChatRequestSchema,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> TrainingChatResponseSchema:
    """
    Send a training feedback message via chat.

    Examples:
    - "This candidate with 10 years Python should match 'Expert Backend Engineer'"
    - "Why did you score Jane 0.65 for this role?"
    - "Improve your matching for 'React' keyword"
    - "Learn that 'Kubernetes' and 'Docker' should have high correlation"
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Get or create session
    session_query = select(TrainingLearningSession).where(
        TrainingLearningSession.id == request.session_id
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        session = TrainingLearningSession(
            id=request.session_id,
            user_id=admin.id,
            status="active",
        )
        db.add(session)

    # TODO: Send message to LLM for training signal extraction
    # For now, mock response
    ai_response = f"I understand: {request.message[:50]}... Learning from this feedback."

    # Create chat message
    message = TrainingChatMessage(
        id=str(uuid4()),
        user_id=admin.id,
        session_id=request.session_id,
        user_message=request.message,
        ai_response=ai_response,
        extracted_training_signal=None,  # TODO: Extract from LLM
        feedback_type=None,  # TODO: Determine type
    )

    db.add(message)
    session.message_count = (session.message_count or 0) + 1
    session.last_message_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)

    logger.info(
        f"Training chat message received",
        extra={
            "session_id": request.session_id,
            "message_length": len(request.message),
            "user_id": admin.id,
        },
    )

    return TrainingChatResponseSchema(
        message_id=message.id,
        ai_response=ai_response,
        feedback_type=None,
        extracted_training_signal=None,
        applied_changes=None,
        learning_impact=None,
    )


@router.get(
    "/chat/{session_id}/history",
    response_model=TrainingChatHistorySchema,
    summary="Get chat conversation history",
    description="Retrieve the conversation history for a training session.",
)
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> TrainingChatHistorySchema:
    """Get chat conversation history."""
    # Verify session belongs to user
    session_query = select(TrainingLearningSession).where(
        (TrainingLearningSession.id == session_id)
        & (TrainingLearningSession.user_id == admin.id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get messages
    messages_query = select(TrainingChatMessage).where(
        TrainingChatMessage.session_id == session_id
    )
    messages_result = await db.execute(messages_query)
    messages = messages_result.scalars().all()

    return TrainingChatHistorySchema(
        session_id=session_id,
        messages=[TrainingChatMessageSchema.from_orm(m) for m in messages],
        total_insights=session.insights_extracted or 0,
        total_updates=session.mappings_updated or 0,
        created_at=session.created_at,
    )


@router.post(
    "/session",
    response_model=TrainingLearningSessionSchema,
    summary="Create new training session",
    description="Create a new training conversation session.",
)
async def create_session(
    request: CreateSessionRequestSchema,
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> TrainingLearningSessionSchema:
    """Create new training session."""
    session = TrainingLearningSession(
        id=str(uuid4()),
        user_id=admin.id,
        title=request.title or "Untitled Session",
        status="active",
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return TrainingLearningSessionSchema.from_orm(session)


# ─ Learning Status ──────────────────────────────────────────────────────────


@router.get(
    "/learning-status",
    response_model=LearningStatusSchema,
    summary="Get learning system status",
    description="Get current status of the autonomous learning system.",
)
async def get_learning_status(
    db: AsyncSession = Depends(get_session),
    admin: User = Depends(verify_admin),
) -> LearningStatusSchema:
    """Get learning system status."""
    # Count active uploads
    uploads_query = select(TrainingDataUpload).where(
        TrainingDataUpload.status == "processing"
    )
    uploads_result = await db.execute(uploads_query)
    active_uploads = len(uploads_result.scalars().all())

    # Count active sessions
    sessions_query = select(TrainingLearningSession).where(
        TrainingLearningSession.status == "active"
    )
    sessions_result = await db.execute(sessions_query)
    active_sessions = len(sessions_result.scalars().all())

    # Count pending items
    pending_query = select(TrainingDataItem).where(
        TrainingDataItem.applied_to_training == False
    )
    pending_result = await db.execute(pending_query)
    pending_items = len(pending_result.scalars().all())

    return LearningStatusSchema(
        is_learning=active_uploads > 0 or active_sessions > 0,
        active_uploads=active_uploads,
        active_chat_sessions=active_sessions,
        pending_items=pending_items,
        learning_metrics=LearningMetricsSchema(
            total_feedback_samples=0,  # TODO: Calculate
            total_insights_extracted=0,  # TODO: Calculate
            capability_mappings_learned=0,  # TODO: Calculate
            credential_equivalencies_discovered=0,  # TODO: Calculate
            success_patterns_identified=0,  # TODO: Calculate
            match_accuracy_improvement=0.0,  # TODO: Calculate
            hire_success_improvement=0.0,  # TODO: Calculate
            capability_coverage_improvement=0.0,  # TODO: Calculate
            last_learning_at=datetime.utcnow(),
            learning_velocity=0.0,  # TODO: Calculate
        ),
    )
