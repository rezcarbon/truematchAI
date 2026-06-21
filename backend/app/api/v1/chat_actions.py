"""Endpoints for action confirmation and execution in manual mode."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.deps import get_current_user
from app.database import get_session
from app.models.user import User
from app.models.chat import ChatMessage, ChatSession
from app.agents.action_executor import ActionExecutor
from app.agents.agent_tools import tools_for_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/actions", tags=["chat"])


class ActionConfirmation(BaseModel):
    """Confirmation for an action."""

    message_id: str
    action_id: str
    confirmed: bool
    notes: Optional[str] = None


class ActionConfirmationResponse(BaseModel):
    """Response after confirming an action."""

    action_id: str
    status: str
    result: Optional[dict] = None
    executed_at: Optional[str] = None


@router.post("/confirm", response_model=ActionConfirmationResponse)
async def confirm_action(
    confirmation: ActionConfirmation,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Confirm or reject a pending action from agent response.

    When an agent generates an action in manual mode (not autonomous),
    the action is marked as "pending" and user must confirm/reject.
    This endpoint processes that confirmation.
    """
    try:
        # Load the chat message containing the action
        stmt = select(ChatMessage).where(ChatMessage.id == UUID(confirmation.message_id))
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        # Verify user owns this message (ChatMessage has no relationship to the
        # session, so look it up explicitly rather than via a lazy attribute).
        session = await db.get(ChatSession, message.session_id)
        if not session or session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized",
            )

        # Find the action in message.actions_taken
        actions = message.actions_taken or []
        action = next((a for a in actions if a.get("id") == confirmation.action_id), None)

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found in message",
            )

        if confirmation.confirmed:
            # Re-check role authorization at execution time — the tool scoping
            # applied when the action was generated is not sufficient on its own
            # (the stored action could be confirmed by a user whose role no
            # longer permits it). Deny if the action type isn't in the user's
            # current toolset.
            allowed_types = {t["name"] for t in tools_for_role(user.role)}
            if action.get("type") not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your role may not execute '{action.get('type')}' actions",
                )

            # Execute the action
            logger.info(
                "Executing confirmed action",
                extra={
                    "action_id": confirmation.action_id,
                    "user_id": str(user.id),
                },
            )

            # Tag the action with its origin session so a durable plan records
            # where it came from (used by the plan-status endpoints).
            action["session_id"] = str(message.session_id)

            # Execute the action
            executed = await ActionExecutor.execute_actions(
                [action],
                user,
                db,
                autonomous=True,  # Execute it now
            )

            # Persist the new action status back onto the stored message so the
            # confirm flow is idempotent and the UI reflects the outcome.
            new_status = executed[0].get("status") if executed else "failed"
            for a in actions:
                if a.get("id") == confirmation.action_id:
                    a["status"] = new_status
                    a["result"] = executed[0].get("result") if executed else None
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(message, "actions_taken")
            await db.commit()

            if new_status == "completed":
                return {
                    "action_id": confirmation.action_id,
                    "status": "executed",
                    "result": executed[0].get("result"),
                    "executed_at": executed[0].get("executed_at"),
                }
            else:
                return {
                    "action_id": confirmation.action_id,
                    "status": "failed",
                    "result": executed[0].get("result") if executed else None,
                }

        else:
            # Reject the action
            logger.info(
                "Action rejected by user",
                extra={
                    "action_id": confirmation.action_id,
                    "user_id": str(user.id),
                    "notes": confirmation.notes,
                },
            )

            return {
                "action_id": confirmation.action_id,
                "status": "rejected",
                "result": {"reason": confirmation.notes or "User rejected action"},
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process action confirmation",
        )


@router.get("/pending")
async def get_pending_actions(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get all pending actions in a chat session that need user confirmation.

    Useful for building a separate action queue UI.
    """
    try:
        from app.models.chat import ChatSession

        # Load session
        session = await db.get(ChatSession, UUID(session_id))
        if not session or session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized",
            )

        # Find all messages with pending actions
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == UUID(session_id)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        pending = []
        for message in messages:
            actions = message.actions_taken or []
            for action in actions:
                if action.get("status") == "pending" and not action.get("autonomous_mode"):
                    pending.append({
                        "message_id": str(message.id),
                        "action_id": action.get("id"),
                        "type": action.get("type"),
                        "description": action.get("description"),
                        "created_at": message.created_at.isoformat() if message.created_at else None,
                    })

        return pending

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pending actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending actions",
        )
