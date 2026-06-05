"""
Notification system API
Handles: in-app notifications, email notifications, preferences, history
Production-ready implementation with database persistence
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, time
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user
from app.models import Notification, NotificationPreference
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============================================================================
# Pydantic Schemas
# ============================================================================
class NotificationResponse(BaseModel):
    """Notification response schema"""
    id: str = Field(..., description="Notification ID")
    type: str = Field(..., description="Notification type (interview_scheduled, etc.)")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    timestamp: str = Field(..., description="ISO 8601 creation timestamp")
    read: bool = Field(..., description="Whether notification has been read")
    action_url: Optional[str] = Field(None, description="Optional action URL")

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notifications response"""
    notifications: List[NotificationResponse]
    total: int
    limit: int
    offset: int


class NotificationPreferenceResponse(BaseModel):
    """Notification preference response schema"""
    user_id: str
    email_notifications: bool
    in_app_notifications: bool
    notification_types: dict
    quiet_hours: dict

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Notification preference update schema"""
    email_notifications: Optional[bool] = None
    in_app_notifications: Optional[bool] = None
    notification_types: Optional[dict] = None
    quiet_hours: Optional[dict] = None


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    read: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get user's notifications with pagination.
    Supports filtering by read status.

    - **limit**: Number of notifications to return (1-100, default 20)
    - **offset**: Starting position for pagination
    - **read**: Filter by read status (null = all, true = read only, false = unread only)
    """
    try:
        # Build query
        query = select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.deleted_at.is_(None),
            )
        )

        # Apply read filter if specified
        if read is not None:
            query = query.where(Notification.read == read)

        # Get total count
        count_query = select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.deleted_at.is_(None),
            )
        )
        if read is not None:
            count_query = count_query.where(Notification.read == read)

        count_result = await db.execute(select(Notification).count())
        total = count_result.scalar() or 0

        # Order by created_at descending and apply pagination
        query = query.order_by(desc(Notification.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        notifications = result.scalars().all()

        return {
            "notifications": [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "title": n.title,
                    "message": n.message,
                    "timestamp": n.created_at.isoformat(),
                    "read": n.read,
                    "action_url": n.action_url,
                }
                for n in notifications
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}", extra={"user_id": str(current_user.id)})
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Mark a single notification as read.
    Only the owner of the notification can mark it as read.
    """
    try:
        # Parse UUID
        try:
            notif_id = UUID(notification_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification ID format")

        # Fetch and verify ownership
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notif_id,
                    Notification.user_id == current_user.id,
                )
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Update notification
        notification.read = True
        notification.read_at = datetime.utcnow()
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        logger.info(
            "Notification marked as read",
            extra={"notification_id": notification_id, "user_id": str(current_user.id)}
        )

        return {
            "id": str(notification.id),
            "read": True,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error marking notification as read: {str(e)}",
            extra={"notification_id": notification_id, "user_id": str(current_user.id)}
        )
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.post("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Mark all unread notifications as read for the current user.
    """
    try:
        # Fetch all unread notifications for user
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == current_user.id,
                    Notification.read == False,
                    Notification.deleted_at.is_(None),
                )
            )
        )
        notifications = result.scalars().all()

        # Update all to read
        now = datetime.utcnow()
        for notification in notifications:
            notification.read = True
            notification.read_at = now

        await db.commit()

        logger.info(
            f"Marked {len(notifications)} notifications as read",
            extra={"user_id": str(current_user.id), "count": len(notifications)}
        )

        return {
            "message": "All notifications marked as read",
            "updated_count": len(notifications),
            "updated_at": now.isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Error marking all notifications as read: {str(e)}",
            extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(status_code=500, detail="Failed to update notifications")


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get user's notification preferences.
    If preferences don't exist, returns defaults.
    """
    try:
        # Try to fetch existing preferences
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == current_user.id
            )
        )
        prefs = result.scalar_one_or_none()

        # If not found, create default preferences
        if not prefs:
            prefs = NotificationPreference(
                user_id=current_user.id,
                email_notifications=True,
                in_app_notifications=True,
                notification_types={
                    "interview_scheduled": True,
                    "scorecard_request": True,
                    "candidate_advanced": True,
                    "pipeline_update": True,
                    "system_alerts": True,
                },
                quiet_hours_enabled=False,
                quiet_hours_start=None,
                quiet_hours_end=None,
            )
            db.add(prefs)
            await db.commit()
            await db.refresh(prefs)

        logger.info(
            "Notification preferences fetched",
            extra={"user_id": str(current_user.id)}
        )

        return {
            "user_id": str(prefs.user_id),
            "email_notifications": prefs.email_notifications,
            "in_app_notifications": prefs.in_app_notifications,
            "notification_types": prefs.notification_types,
            "quiet_hours": {
                "enabled": prefs.quiet_hours_enabled,
                "start": prefs.quiet_hours_start or "22:00",
                "end": prefs.quiet_hours_end or "08:00",
            },
        }

    except Exception as e:
        logger.error(
            f"Error fetching notification preferences: {str(e)}",
            extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(status_code=500, detail="Failed to fetch preferences")


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update user's notification preferences.
    Only provided fields are updated; missing fields retain current values.
    """
    try:
        # Fetch existing preferences or create new
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == current_user.id
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            # Create new with defaults + updates
            prefs = NotificationPreference(
                user_id=current_user.id,
                email_notifications=preferences.email_notifications if preferences.email_notifications is not None else True,
                in_app_notifications=preferences.in_app_notifications if preferences.in_app_notifications is not None else True,
                notification_types=preferences.notification_types or {
                    "interview_scheduled": True,
                    "scorecard_request": True,
                    "candidate_advanced": True,
                    "pipeline_update": True,
                    "system_alerts": True,
                },
            )
            db.add(prefs)
        else:
            # Update existing preferences
            if preferences.email_notifications is not None:
                prefs.email_notifications = preferences.email_notifications
            if preferences.in_app_notifications is not None:
                prefs.in_app_notifications = preferences.in_app_notifications
            if preferences.notification_types is not None:
                prefs.notification_types = preferences.notification_types
            if preferences.quiet_hours is not None:
                prefs.quiet_hours_enabled = preferences.quiet_hours.get("enabled", False)
                prefs.quiet_hours_start = preferences.quiet_hours.get("start")
                prefs.quiet_hours_end = preferences.quiet_hours.get("end")

            prefs.updated_at = datetime.utcnow()
            db.add(prefs)

        await db.commit()
        await db.refresh(prefs)

        logger.info(
            "Notification preferences updated",
            extra={"user_id": str(current_user.id)}
        )

        return {
            "user_id": str(prefs.user_id),
            "email_notifications": prefs.email_notifications,
            "in_app_notifications": prefs.in_app_notifications,
            "notification_types": prefs.notification_types,
            "quiet_hours": {
                "enabled": prefs.quiet_hours_enabled,
                "start": prefs.quiet_hours_start or "22:00",
                "end": prefs.quiet_hours_end or "08:00",
            },
        }

    except Exception as e:
        logger.error(
            f"Error updating notification preferences: {str(e)}",
            extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Delete (soft delete) a notification.
    The notification is marked as deleted but remains in database for audit.
    """
    try:
        # Parse UUID
        try:
            notif_id = UUID(notification_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification ID format")

        # Fetch and verify ownership
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notif_id,
                    Notification.user_id == current_user.id,
                )
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Soft delete notification
        notification.deleted_at = datetime.utcnow()
        db.add(notification)
        await db.commit()

        logger.info(
            "Notification deleted",
            extra={"notification_id": notification_id, "user_id": str(current_user.id)}
        )

        return {
            "id": str(notification.id),
            "deleted": True,
            "deleted_at": notification.deleted_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting notification: {str(e)}",
            extra={"notification_id": notification_id, "user_id": str(current_user.id)}
        )
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.post("/clear-all")
async def clear_all_notifications(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Clear (soft delete) all notifications for the current user.
    The notifications remain in the database marked as deleted.
    """
    try:
        # Fetch all non-deleted notifications for user
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == current_user.id,
                    Notification.deleted_at.is_(None),
                )
            )
        )
        notifications = result.scalars().all()

        # Soft delete all
        now = datetime.utcnow()
        for notification in notifications:
            notification.deleted_at = now

        await db.commit()

        logger.info(
            f"Cleared {len(notifications)} notifications",
            extra={"user_id": str(current_user.id), "count": len(notifications)}
        )

        return {
            "user_id": str(current_user.id),
            "message": "All notifications cleared",
            "cleared_count": len(notifications),
            "cleared_at": now.isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Error clearing notifications: {str(e)}",
            extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(status_code=500, detail="Failed to clear notifications")
