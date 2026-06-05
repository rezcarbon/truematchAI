"""Notifications endpoints for alerts and system messages."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser, DBSession
from app.models import Notification

router = APIRouter()
logger = logging.getLogger("truematch.notifications")


class NotificationResponse:
    """Response schema for notification data"""

    def __init__(self, notification: Notification):
        self.id = str(notification.id)
        self.title = notification.title
        self.message = notification.message
        self.type = notification.type
        self.read = notification.read
        self.action_url = notification.action_url
        self.created_at = notification.created_at.isoformat()
        self.read_at = notification.read_at.isoformat() if notification.read_at else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "read": self.read,
            "action_url": self.action_url,
            "created_at": self.created_at,
            "read_at": self.read_at,
        }


@router.get("/notifications")
async def list_notifications(
    user: CurrentUser,
    db: DBSession,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List notifications for the current user.

    Args:
        user: Current authenticated user
        db: Database session
        unread_only: If True, only return unread notifications
        limit: Maximum number of notifications to return
        offset: Number of notifications to skip

    Returns:
        Dictionary with unread_count and notifications list
    """
    # Build query
    query = select(Notification).where(Notification.user_id == user.id)

    if unread_only:
        query = query.where(Notification.read == False)

    # Order by created_at descending (newest first)
    query = query.order_by(desc(Notification.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    notifications = result.scalars().all()

    # Get unread count
    unread_query = select(Notification).where(
        Notification.user_id == user.id,
        Notification.read == False,
    )
    unread_result = await db.execute(unread_query)
    unread_count = len(unread_result.scalars().all())

    logger.info(f"Listed {len(notifications)} notifications for user {user.id} (unread: {unread_count})")

    return {
        "unread_count": unread_count,
        "total_count": len(notifications),
        "notifications": [NotificationResponse(n).to_dict() for n in notifications],
    }


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(notification_id: str, user: CurrentUser, db: DBSession) -> None:
    """Mark a notification as read.

    Args:
        notification_id: ID of the notification to mark as read
        user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If notification not found or user doesn't have permission
    """
    try:
        notification_uuid = UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

    # Verify ownership
    query = select(Notification).where(
        Notification.id == notification_uuid,
        Notification.user_id == user.id,
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Update notification
    update_query = (
        update(Notification)
        .where(Notification.id == notification_uuid)
        .values(read=True, read_at=datetime.utcnow())
    )
    await db.execute(update_query)
    await db.commit()

    logger.info(f"Marked notification {notification_id} as read for user {user.id}")


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(user: CurrentUser, db: DBSession) -> None:
    """Mark all notifications as read for the current user.

    Args:
        user: Current authenticated user
        db: Database session
    """
    update_query = (
        update(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.read == False,
        )
        .values(read=True, read_at=datetime.utcnow())
    )
    result = await db.execute(update_query)
    await db.commit()

    logger.info(f"Marked all notifications as read for user {user.id} ({result.rowcount} updated)")


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: str, user: CurrentUser, db: DBSession) -> None:
    """Delete a notification.

    Args:
        notification_id: ID of the notification to delete
        user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If notification not found or user doesn't have permission
    """
    try:
        notification_uuid = UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

    # Verify ownership and delete
    query = select(Notification).where(
        Notification.id == notification_uuid,
        Notification.user_id == user.id,
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notification)
    await db.commit()

    logger.info(f"Deleted notification {notification_id} for user {user.id}")
