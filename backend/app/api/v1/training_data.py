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

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select

from app.deps import DBSession, CurrentAdmin
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
    db: DBSession,
    admin: CurrentAdmin,
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

    # Read file content
    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Create upload record
    upload = TrainingDataUpload(
        id=uuid4(),
        user_id=admin.id,
        filename=file.filename,
        format=file_format,
        status="pending",
        row_count=0,
    )

    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    logger.info(
        f"Training data upload started",
        extra={
            "upload_id": str(upload.id),
            "filename": file.filename,
            "format": file_format,
            "user_id": str(admin.id),
            "file_size": len(file_content),
        },
    )

    # Queue background job to process file
    # Using a simple background task system (can be replaced with Celery/RQ)
    try:
        import asyncio
        from app.workers.training_jobs import TrainingJobProcessor

        # Start background processing task
        asyncio.create_task(
            TrainingJobProcessor().process_upload(upload.id, file_content, db)
        )

        logger.info(
            f"Upload job queued",
            extra={"upload_id": str(upload.id)},
        )
    except Exception as e:
        logger.error(f"Error queuing upload job: {e}")
        # Job queuing failed but upload record created
        # User can check status via GET endpoint

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
    db: DBSession,
    admin: CurrentAdmin,
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
    db: DBSession,
    admin: CurrentAdmin,
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
    db: DBSession,
    admin: CurrentAdmin,
) -> UploadResultSchema:
    """Get upload processing status and results."""
    upload_uuid = UUID(upload_id) if isinstance(upload_id, str) else upload_id

    query = select(TrainingDataUpload).where(
        (TrainingDataUpload.id == upload_uuid) & (TrainingDataUpload.user_id == admin.id)
    )

    result = await db.execute(query)
    upload = result.scalar_one_or_none()

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Get associated insights batch
    from app.models.training_data import TrainingInsightBatch

    insights_query = select(TrainingInsightBatch).where(
        TrainingInsightBatch.source_id == upload_uuid
    )
    insights_result = await db.execute(insights_query)
    insights_batch = insights_result.scalar_one_or_none()

    improvement_delta = {}
    new_capabilities = []
    updated_mappings = []
    processing_time = 0.0

    if insights_batch:
        improvement_delta = {
            "match_accuracy": insights_batch.match_accuracy_after - insights_batch.match_accuracy_before,
            **insights_batch.improvement_metrics,
        }
        new_capabilities = insights_batch.new_capabilities
        updated_mappings = insights_batch.updated_mappings
        processing_time = (insights_batch.created_at - upload.created_at).total_seconds()

    return UploadResultSchema(
        upload_id=str(upload.id),
        items_processed=upload.items_processed,
        items_failed=upload.items_failed,
        insights_extracted=upload.insights_extracted,
        new_capabilities=new_capabilities,
        updated_mappings=updated_mappings,
        improvement_delta=improvement_delta,
        processing_time_seconds=processing_time,
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
    db: DBSession,
    admin: CurrentAdmin,
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
        await db.commit()

    # Get conversation history
    history_query = (
        select(TrainingChatMessage)
        .where(TrainingChatMessage.session_id == request.session_id)
        .order_by(TrainingChatMessage.created_at.asc())
    )
    history_result = await db.execute(history_query)
    messages = history_result.scalars().all()

    # Convert to conversation history format
    conversation_history = []
    for msg in messages:
        if msg.user_message:
            conversation_history.append(
                {"role": "user", "content": msg.user_message}
            )
        if msg.ai_response:
            conversation_history.append(
                {"role": "assistant", "content": msg.ai_response}
            )

    # Process message through Claude chat engine
    from app.engines.training_chat_engine import TrainingChatEngine

    chat_engine = TrainingChatEngine()
    result = await chat_engine.process_message(request.message, conversation_history)

    ai_response = result.get("ai_response", "")
    training_signal = result.get("extracted_training_signal")
    feedback_type = result.get("feedback_type")

    # Create chat message record
    message = TrainingChatMessage(
        id=str(uuid4()),
        user_id=admin.id,
        session_id=request.session_id,
        user_message=request.message,
        ai_response=ai_response,
        extracted_training_signal=training_signal,
        feedback_type=feedback_type,
    )

    db.add(message)
    session.message_count = (session.message_count or 0) + 1
    session.last_message_at = datetime.utcnow()

    # Track insights and mappings if training signal extracted
    if training_signal:
        session.insights_extracted = (session.insights_extracted or 0) + 1
        if feedback_type in ["mapping_correction", "credential_equivalency"]:
            session.mappings_updated = (session.mappings_updated or 0) + 1

    await db.commit()
    await db.refresh(message)

    # Analyze learning impact
    learning_impact = await chat_engine.analyze_learning_impact(
        [
            {
                "feedback_type": msg.feedback_type,
                "description": msg.extracted_training_signal.get("description")
                if msg.extracted_training_signal
                else "",
            }
            for msg in messages + [message]
            if msg.feedback_type
        ]
    )

    logger.info(
        f"Training chat message processed",
        extra={
            "session_id": request.session_id,
            "message_length": len(request.message),
            "feedback_type": feedback_type,
            "signal_extracted": training_signal is not None,
            "user_id": str(admin.id),
        },
    )

    return TrainingChatResponseSchema(
        message_id=message.id,
        ai_response=ai_response,
        feedback_type=feedback_type,
        extracted_training_signal=training_signal,
        applied_changes=training_signal.get("action") if training_signal else None,
        learning_impact=learning_impact,
    )


@router.get(
    "/chat/{session_id}/history",
    response_model=TrainingChatHistorySchema,
    summary="Get chat conversation history",
    description="Retrieve the conversation history for a training session.",
)
async def get_chat_history(
    session_id: str,
    db: DBSession,
    admin: CurrentAdmin,
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
    db: DBSession,
    admin: CurrentAdmin,
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
    db: DBSession,
    admin: CurrentAdmin,
) -> LearningStatusSchema:
    """Get learning system status."""
    from sqlalchemy import func

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

    # Calculate metrics
    from app.models.training_data import TrainingInsightBatch

    # Total items processed
    total_items_query = select(func.count(TrainingDataItem.id))
    total_items_result = await db.execute(total_items_query)
    total_feedback = total_items_result.scalar() or 0

    # Latest insight batch
    latest_batch_query = (
        select(TrainingInsightBatch)
        .order_by(TrainingInsightBatch.created_at.desc())
        .limit(1)
    )
    latest_batch_result = await db.execute(latest_batch_query)
    latest_batch = latest_batch_result.scalar_one_or_none()

    # Get improvement metrics
    last_learning_at = latest_batch.created_at if latest_batch else datetime.utcnow()
    match_accuracy_improvement = (
        (latest_batch.match_accuracy_after - latest_batch.match_accuracy_before)
        if latest_batch
        else 0.0
    )

    # Count capabilities learned
    unique_capabilities_query = select(
        func.count(func.distinct(TrainingDataItem.extracted_capabilities))
    ).where(TrainingDataItem.extracted_capabilities.isnot(None))
    unique_capabilities_result = await db.execute(unique_capabilities_query)
    capability_mappings_learned = unique_capabilities_result.scalar() or 0

    return LearningStatusSchema(
        is_learning=active_uploads > 0 or active_sessions > 0,
        active_uploads=active_uploads,
        active_chat_sessions=active_sessions,
        pending_items=pending_items,
        learning_metrics=LearningMetricsSchema(
            total_feedback_samples=total_feedback,
            total_insights_extracted=0,  # From insight batches
            capability_mappings_learned=capability_mappings_learned,
            credential_equivalencies_discovered=0,  # From analysis
            success_patterns_identified=len(latest_batch.new_success_patterns)
            if latest_batch
            else 0,
            match_accuracy_improvement=match_accuracy_improvement,
            hire_success_improvement=0.0,  # From metrics
            capability_coverage_improvement=0.0,  # From metrics
            last_learning_at=last_learning_at,
            learning_velocity=total_feedback / 7 if total_feedback > 0 else 0.0,  # items per day estimate
        ),
    )
