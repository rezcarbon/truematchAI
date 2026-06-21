"""
WebSocket API endpoints for real-time updates
Handles: pipeline updates, interview notifications, presence tracking
"""

import logging
from uuid import UUID
from app.core.clock import utcnow

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy import update

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
    except Exception:
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
                                delivered_at=utcnow()
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


@router.websocket("/progress/{resource_id}")
async def websocket_progress(
    websocket: WebSocket,
    resource_id: str,
    token: str = Query(None),
):
    """
    WebSocket endpoint for real-time task progress updates.
    Broadcasts: CV analysis progress, training upload progress, assessment pipeline progress.

    Clients can subscribe to progress updates for specific resources (analysis_id, upload_id, etc.)
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

        # Import here to avoid circular imports
        from app.workers.realtime_progress import get_progress_tracker

        tracker = get_progress_tracker()

        # Subscribe to progress updates for this resource
        async def send_progress(event):
            """Send progress event to client."""
            try:
                await websocket.send_json(event.to_dict())
            except Exception as e:
                logger.error(f"Failed to send progress event: {e}")

        # Subscribe to assessment-specific progress
        sub_id = tracker.subscribe_to_assessment(resource_id, send_progress)

        logger.info(
            "Client connected to progress updates",
            extra={
                "resource_id": resource_id,
                "user_id": str(user_id),
                "subscription_id": sub_id,
            },
        )

        # Send any existing progress history for this resource
        existing_events = tracker.get_assessment_events(resource_id)
        for event in existing_events:
            await websocket.send_json(event)

        # Keep connection open and listen for ping/pong
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": utcnow().isoformat(),
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in progress WebSocket: {e}")
                break

        # Unsubscribe on disconnect
        tracker.unsubscribe_from_assessment(resource_id, send_progress)
        logger.info(
            "Client disconnected from progress updates",
            extra={"resource_id": resource_id, "user_id": str(user_id)},
        )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Progress WebSocket error: {e}")
