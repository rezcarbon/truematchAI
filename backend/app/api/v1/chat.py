"""Chat API endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message, ConversationStatus, MessageRole
from app.schemas.chat import (
    ConversationResponse, ConversationDetailResponse, ConversationCreate,
    MessageResponse, MessageCreate, MessageListResponse
)

logger = logging.getLogger("truematch.chat_api")

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new conversation."""
    try:
        conversation = Conversation(
            user_id=user.id,
            title=request.title or "New Chat"
        )
        db.add(conversation)
        await db.flush()
        await db.commit()
        
        logger.info(f"Conversation created: {conversation.id} for user {user.id}")
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "status": conversation.status.value,
            "message_count": conversation.message_count,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "archived_at": conversation.archived_at,
        }
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create conversation")


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list:
    """List all conversations for the current user."""
    try:
        stmt = select(Conversation).where(
            and_(Conversation.user_id == user.id, Conversation.status != ConversationStatus.closed)
        ).limit(limit).offset(offset).order_by(Conversation.updated_at.desc())
        
        result = await db.scalars(stmt)
        conversations = list(result.all())
        
        return [
            {
                "id": c.id,
                "user_id": c.user_id,
                "title": c.title,
                "status": c.status.value,
                "message_count": c.message_count,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "archived_at": c.archived_at,
            }
            for c in conversations
        ]
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list conversations")


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific conversation with messages."""
    try:
        conversation = await db.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        messages_result = await db.scalars(stmt)
        messages = list(messages_result.all())
        
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "status": conversation.status.value,
            "message_count": conversation.message_count,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "archived_at": conversation.archived_at,
            "messages": [
                {
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "user_id": m.user_id,
                    "content": m.content,
                    "role": m.role.value,
                    "metadata": m.message_metadata,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                }
                for m in messages
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get conversation")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: UUID,
    request: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send a message in a conversation."""
    try:
        conversation = await db.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        
        message = Message(
            conversation_id=conversation_id,
            user_id=user.id,
            role=MessageRole(request.role) if request.role else MessageRole.user,
            content=request.content,
            message_metadata=request.metadata,
        )
        db.add(message)
        conversation.message_count += 1
        await db.flush()
        await db.commit()
        
        logger.info(f"Message created: {message.id} in conversation {conversation_id}")
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "user_id": message.user_id,
            "content": message.content,
            "role": message.role.value,
            "metadata": message.message_metadata,
            "created_at": message.created_at,
            "updated_at": message.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message")


@router.get("/messages", response_model=MessageListResponse)
async def list_messages(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    conversation_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
) -> dict:
    """List messages with optional filtering."""
    try:
        offset = (page - 1) * limit
        
        if conversation_id:
            conversation = await db.get(Conversation, conversation_id)
            if not conversation or conversation.user_id != user.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
            
            stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit).offset(offset)
        else:
            stmt = select(Message).where(Message.user_id == user.id).order_by(Message.created_at.desc()).limit(limit).offset(offset)
        
        messages_result = await db.scalars(stmt)
        messages = list(messages_result.all())
        
        return {
            "messages": [
                {
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "user_id": m.user_id,
                    "content": m.content,
                    "role": m.role.value,
                    "metadata": m.message_metadata,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                }
                for m in messages
            ],
            "total": len(messages),
            "page": page,
            "page_size": limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list messages")
