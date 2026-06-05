"""Notifications endpoints for alerts and system messages."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, status

from app.deps import CurrentUser, DBSession

router = APIRouter()
logger = logging.getLogger("truematch.notifications")


class MockNotification:
    """Mock notification for MVP - replace with DB model in v2"""

    def __init__(
        self,
        id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        read: bool = False,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.title = title
        self.message = message
        self.notification_type = notification_type
        self.read = read
        self.created_at = created_at or datetime.utcnow()


@router.get("/notifications")
async def list_notifications(user: CurrentUser, db: DBSession) -> dict:
    """List unread notifications for the current user.

    Returns a list of notifications in reverse chronological order.
    """
    # MVP: Return mock notifications
    # In production, fetch from database with: db.execute(
    #   select(Notification).where(Notification.user_id == user.id)
    # )

    mock_notifications = [
        MockNotification(
            id="notif-1",
            title="CV Analysis Complete",
            message="Your CV analysis for 'Senior Backend Engineer' is ready for review.",
            notification_type="success",
            read=False,
            created_at=datetime.utcnow() - timedelta(hours=1),
        ),
        MockNotification(
            id="notif-2",
            title="New Job Match",
            message="2 new positions match your profile based on recent CV analysis.",
            notification_type="info",
            read=False,
            created_at=datetime.utcnow() - timedelta(hours=3),
        ),
    ]

    return {
        "unread_count": len([n for n in mock_notifications if not n.read]),
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.notification_type,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
            }
            for n in mock_notifications
        ],
    }


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: str, user: CurrentUser, db: DBSession
) -> None:
    """Mark a notification as read."""
    # MVP: Mock implementation
    # In production: db.execute(
    #   update(Notification).where(Notification.id == notification_id)
    #   .values(read=True)
    # )
    logger.info(f"Marked notification {notification_id} as read for user {user.id}")
    return None


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(user: CurrentUser, db: DBSession) -> None:
    """Mark all notifications as read for the current user."""
    # MVP: Mock implementation
    # In production: db.execute(
    #   update(Notification).where(Notification.user_id == user.id)
    #   .values(read=True)
    # )
    logger.info(f"Marked all notifications as read for user {user.id}")
    return None
