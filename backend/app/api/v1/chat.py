"""Conversational chat endpoints for AI-native interface."""
import logging
from datetime import datetime
from app.core.clock import utcnow
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import func, select, String
from pydantic import BaseModel, Field

from app.models.chat import ChatSession, ChatMessage
from app.deps import CurrentUser, DBSession
from app.agents.agent_router import get_agent_for_user

logger = logging.getLogger("truematch.chat")
router = APIRouter(prefix="/chat", tags=["chat"])


# Models
class ChatMessageRequest(BaseModel):
    """User message in a chat."""
    session_id: str
    message: str
    mode: str = Field(
        "general",
        description="Chat mode: 'career_coach', 'interview_prep', 'general'",
    )
    history: list[dict] = Field(default_factory=list)
    explicit_objective: Optional[str] = Field(
        None,
        description="Optional explicit objective override for persona selection (e.g., 'interview_prep', 'candidate_screening')",
    )


class ActionDetail(BaseModel):
    """Details of an action taken by the agent."""
    id: str
    description: str
    status: str  # pending, completed, failed
    result: Optional[Any] = None
    type: Optional[str] = None
    requires_confirmation: bool = False


class PersonaInfo(BaseModel):
    """Information about the active persona."""
    id: str
    name: str
    title: str


class ChatMessageResponse(BaseModel):
    """Response from chat agent."""
    response: str
    message_id: str
    actions: list[ActionDetail] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    persona: Optional[PersonaInfo] = Field(None, description="Active persona information")
    objective: Optional[str] = Field(None, description="Detected user objective")
    mode: Optional[str] = Field(None, description="Conversation mode (general, supportive, analytical, etc.)")


class ChatSessionDetail(BaseModel):
    """A chat session."""
    id: str
    title: str
    created_at: datetime
    last_message_at: datetime
    message_count: int


class ChatSessionResponse(BaseModel):
    """Response for session creation."""
    id: str
    title: str


class ChatSessionMessagesResponse(BaseModel):
    """Session with its messages."""
    id: str
    title: str
    messages: list[dict]


class FileUploadResponse(BaseModel):
    """Response from file upload."""
    file_id: str
    filename: str
    size: int
    type: str
    upload_time: datetime


# Endpoints


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: dict,
    current_user: CurrentUser,
    db: DBSession,
) -> ChatSessionResponse:
    """Create a new chat session."""
    now = utcnow()
    session = ChatSession(
        user_id=current_user.id,
        title=request.get("title", f"Chat - {now.strftime('%Y-%m-%d')}"),
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    await db.commit()

    return ChatSessionResponse(
        id=str(session.id),
        title=session.title,
    )


@router.get("/sessions", response_model=list[ChatSessionDetail])
async def list_chat_sessions(
    current_user: CurrentUser,
    db: DBSession,
) -> list[ChatSessionDetail]:
    """List all chat sessions for the user."""
    sessions = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.last_message_at.desc())
    )

    results = sessions.scalars().all()

    # Message counts per session in a single query (ChatSession has no eager
    # `messages` relationship; lazy access would fail under async).
    counts: dict = {}
    if results:
        count_rows = await db.execute(
            select(ChatMessage.session_id, func.count(ChatMessage.id))
            .where(ChatMessage.session_id.in_([s.id for s in results]))
            .group_by(ChatMessage.session_id)
        )
        counts = {row[0]: row[1] for row in count_rows.all()}

    return [
        ChatSessionDetail(
            id=str(s.id),
            title=s.title,
            created_at=s.created_at,
            last_message_at=s.last_message_at or s.created_at,
            message_count=counts.get(s.id, 0),
        )
        for s in results
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionMessagesResponse)
async def get_chat_session(
    session_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> ChatSessionMessagesResponse:
    """Get a specific chat session with all messages."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")

    session = await db.get(ChatSession, session_uuid)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_uuid)
        .order_by(ChatMessage.created_at.asc())
    )

    msg_list = messages.scalars().all()

    return ChatSessionMessagesResponse(
        id=str(session.id),
        title=session.title,
        messages=[
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat(),
                "actions_taken": m.actions_taken or [],
            }
            for m in msg_list
        ],
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a chat session."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")

    session = await db.get(ChatSession, session_uuid)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await db.delete(session)
    await db.commit()


@router.post("/", response_model=ChatMessageResponse)
async def chat(
    request: ChatMessageRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ChatMessageResponse:
    """Send a message to the chat agent.

    Routes to appropriate agent based on user role and conversation intent.
    Executes actions and returns response.
    """
    try:
        session_uuid = UUID(request.session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")

    # Get session
    session = await db.get(ChatSession, session_uuid)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Store user message
    now = utcnow()
    user_msg = ChatMessage(
        session_id=session_uuid,
        role="user",
        content=request.message,
        created_at=now,
        updated_at=now,
    )
    db.add(user_msg)
    await db.commit()

    # Get appropriate agent for this user (with custom config if available)
    # TODO: Extract company_id from user.company_id or request context
    agent = await get_agent_for_user(current_user.id, current_user.role, db, company_id=None)

    # Build candidate context for career coach mode
    candidate_context = None
    if request.mode == "career_coach":
        from app.schemas.job_search import CandidateContext
        from app.models.saved_job import SavedJob
        from app.models.assessment import Assessment

        # Fetch candidate context
        saved_jobs_count = await db.scalar(
            select(func.count()).select_from(SavedJob)
            .where(SavedJob.user_id == current_user.id)
        ) or 0

        assessments_count = await db.scalar(
            select(func.count()).select_from(Assessment)
            .where(Assessment.user_id == current_user.id)
        ) or 0

        candidate_context = CandidateContext(
            user_id=current_user.id,
            name=getattr(current_user, "full_name", None),
            current_role=getattr(current_user, "current_title", None),
            target_roles=getattr(current_user, "target_roles", None),
            saved_jobs=saved_jobs_count,
            recent_assessments=assessments_count,
        )

    # Track the real LLM cost of generating this turn.
    from app.core.llm_usage import reset_usage, get_usage
    reset_usage()

    # Generate response with session memory integration
    # ✨ NEW: Use persona-aware response if available
    persona_info = None
    objective = None
    conv_mode = None

    try:
        # Check if agent supports persona system (CandidateAgent/RecruiterAgent)
        if hasattr(agent, 'respond_with_persona'):
            persona_response = await agent.respond_with_persona(
                message=request.message,
                user_id=str(current_user.id),
                session_id=str(session_uuid),
                chat_mode=request.mode,
                explicit_objective=request.explicit_objective,  # ✨ NEW: Pass explicit objective
            )
            # Extract persona information
            persona_info = persona_response.get("persona")
            objective = persona_response.get("objective")
            conv_mode = persona_response.get("mode")
            response_text = persona_response.get("response")
            actions = []  # Actions extraction would go here
        else:
            # Fall back to regular respond for other agent types
            agent_response = await agent.respond(
                message=request.message,
                history=request.history,
                user=current_user,
                db=db,
                session_id=session_uuid,
                mode=request.mode,
                candidate_context=candidate_context,
            )
            response_text = agent_response.text
            actions = agent_response.actions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}",
        )

    # Charge the real inference cost of this turn to the user's daily budget
    # (previously the budget only counted fixed per-action-type estimates and
    # ignored LLM spend entirely).
    turn_usage = get_usage()
    if turn_usage.cost_usd > 0:
        from app.models.autonomous_settings import AutonomousSettings
        settings_row = (
            await db.execute(
                select(AutonomousSettings).where(AutonomousSettings.user_id == current_user.id)
            )
        ).scalar_one_or_none()
        if settings_row is not None:
            settings_row.record_action(cost=turn_usage.cost_usd)
            await db.commit()
        logger.info(
            "Chat turn cost",
            extra={"user_id": str(current_user.id), **turn_usage.as_dict()},
        )

    # Store assistant message with persona metadata
    msg_now = utcnow()
    # ✨ NEW: Store persona information in message_metadata
    message_metadata = {}
    if persona_info:
        message_metadata["persona_id"] = persona_info.get("id")
        message_metadata["persona_name"] = persona_info.get("name")
    if objective:
        message_metadata["objective"] = objective
    if conv_mode:
        message_metadata["mode"] = conv_mode

    assistant_msg = ChatMessage(
        session_id=session_uuid,
        role="assistant",
        content=response_text,
        actions_taken=actions if 'actions' in locals() else [],
        created_at=msg_now,
        updated_at=msg_now,
        message_metadata=message_metadata if message_metadata else None,  # ✨ NEW: Store persona metadata
    )
    db.add(assistant_msg)

    # Update session last message time
    session.last_message_at = utcnow()

    await db.commit()

    return ChatMessageResponse(
        response=response_text,
        message_id=str(assistant_msg.id),
        actions=[
            ActionDetail(
                id=action["id"],
                description=action["description"],
                status=action["status"],
                result=action.get("result"),
                type=action.get("type"),
                requires_confirmation=action.get("requires_confirmation", False),
            )
            for action in (actions if 'actions' in locals() else [])
        ],
        suggestions=[],  # Suggestions extraction would go here
        # ✨ NEW: Include persona information in response
        persona=PersonaInfo(**persona_info) if persona_info else None,
        objective=objective,
        mode=conv_mode,
    )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> FileUploadResponse:
    """Upload a file for processing (CV, job description, candidates list, etc.)."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename")

    # Read file
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    # For now, return file info
    # In full implementation, would store in S3 or similar
    return FileUploadResponse(
        file_id=str(__import__("uuid").uuid4()),
        filename=file.filename,
        size=len(content),
        type=file.content_type or "unknown",
        upload_time=utcnow(),
    )
