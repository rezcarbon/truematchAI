"""
WebSocket API endpoints for real-time updates
Handles: pipeline updates, interview notifications, presence tracking
"""

import logging
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.manager import manager
from app.core.security import verify_token_from_websocket
from app.database import AsyncSessionLocal
from app.models import Notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/pipeline/{position_id}")
async def websocket_pipeline(
    websocket: WebSocket,
    position_id: str,
    token: str = Query(None),
):
    """
    WebSocket endpoint for real-time pipeline updates
    Broadcasts: candidate stage changes, interview scheduling, scorecard submissions
    """
    try:
        # Verify token
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
            return

        user_id = verify_token_from_websocket(token)
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        # Register connection
        await manager.connect(websocket, position_id, user_id)

        # Listen for messages
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": data.get("timestamp")})

            elif data.get("type") == "pipeline_update":
                # Broadcast pipeline update to all users on this position
                await manager.broadcast_pipeline_update(
                    position_id,
                    data.get("application_id"),
                    data.get("new_stage"),
                )

            elif data.get("type") == "interview_scheduled":
                # Broadcast interview scheduling
                await manager.broadcast_interview_scheduled(
                    position_id,
                    data.get("application_id"),
                    data.get("scheduled_at"),
                )

            elif data.get("type") == "scorecard_submitted":
                # Broadcast scorecard submission
                await manager.broadcast_scorecard_submitted(
                    position_id,
                    data.get("interview_id"),
                    data.get("score"),
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
    except Exception as e:
        await manager.disconnect(websocket, user_id)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(None),
):
    """
    WebSocket endpoint for user-specific notifications
    Broadcasts: interview reminders, scorecard requests, system notifications
    """
    try:
        # Verify token
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
            return

        user_id = verify_token_from_websocket(token)
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        await websocket.accept()

        # Send connected confirmation
        await websocket.send_json({"type": "connected", "user_id": str(user_id)})

        # Listen for notification acknowledgments
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ack":
                # Client acknowledged receipt of notification - mark as delivered in database
                notification_id = data.get("notification_id")
                try:
                    notif_uuid = UUID(notification_id)
                    async with AsyncSessionLocal() as db:
                        # Update notification delivery status
                        stmt = (
                            update(Notification)
                            .where(Notification.id == notif_uuid)
                            .values(
                                delivered=True,
                                delivered_at=datetime.utcnow()
                            )
                        )
                        await db.execute(stmt)
                        await db.commit()
                        logger.info(
                            f"Notification {notification_id} marked as delivered",
                            extra={"user_id": str(user_id), "notification_id": notification_id}
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to mark notification as delivered: {str(e)}",
                        extra={"notification_id": notification_id, "user_id": str(user_id)}
                    )

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
