"""Notification service for creating and managing notifications."""
import logging
from datetime import datetime
from app.core.clock import utcnow
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationPreference
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notification operations."""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        action_url: str = None,
        broadcast_websocket: bool = True,
        idempotency_key: str = None,
    ) -> Notification:
        """
        Create a notification for a user.

        Args:
            db: Database session
            user_id: User to notify
            notification_type: Type of notification (interview_scheduled, etc.)
            title: Notification title
            message: Notification message
            action_url: Optional URL for action
            broadcast_websocket: Whether to broadcast via WebSocket
            idempotency_key: Optional key to prevent duplicate notifications

        Returns:
            Created notification
        """
        try:
            # Check for idempotency key to prevent duplicates
            if idempotency_key:
                # Look for identical notification created recently (within 5 minutes)
                from datetime import timedelta
                recent_cutoff = utcnow() - timedelta(minutes=5)

                existing = await db.scalar(
                    select(Notification).where(
                        and_(
                            Notification.user_id == user_id,
                            Notification.type == notification_type,
                            Notification.action_url == action_url,
                            Notification.created_at > recent_cutoff,
                        )
                    )
                )

                if existing:
                    logger.info(
                        f"Notification already exists (idempotent): {notification_type}",
                        extra={
                            "user_id": str(user_id),
                            "notification_id": str(existing.id),
                            "idempotency_key": idempotency_key,
                        },
                    )
                    return existing

            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                read=False,
                delivered=False,
                email_sent=False,
            )

            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            logger.info(
                f"Notification created: {notification_type}",
                extra={
                    "notification_id": str(notification.id),
                    "user_id": str(user_id),
                    "type": notification_type,
                },
            )

            # Broadcast via WebSocket if enabled
            if broadcast_websocket:
                await manager.send_notification_to_user(
                    str(user_id),
                    {
                        "type": "notification",
                        "notification_id": str(notification.id),
                        "title": title,
                        "message": message,
                        "action_url": action_url,
                        "timestamp": notification.created_at.isoformat(),
                    },
                )

            # Fan out to the user's registered push devices (no-op when no push
            # provider is configured). Best-effort: never fail the notification.
            try:
                from app.services.push_service import send_push_to_user

                await send_push_to_user(
                    db, user_id, title, message, {"action_url": action_url or ""}
                )
            except Exception as push_exc:  # noqa: BLE001
                logger.warning("Push fan-out failed: %s", push_exc)

            return notification

        except Exception as e:
            logger.error(
                f"Failed to create notification: {str(e)}",
                extra={"user_id": str(user_id), "type": notification_type},
            )
            raise

    @staticmethod
    async def mark_as_read(db: AsyncSession, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        try:
            stmt = (
                update(Notification)
                .where(Notification.id == notification_id)
                .values(read=True, read_at=utcnow())
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False

    @staticmethod
    async def mark_as_email_sent(db: AsyncSession, notification_id: UUID) -> bool:
        """Mark a notification as email sent."""
        try:
            stmt = (
                update(Notification)
                .where(Notification.id == notification_id)
                .values(email_sent=True, email_sent_at=utcnow())
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to mark notification as email sent: {str(e)}")
            return False

    @staticmethod
    async def get_user_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> NotificationPreference:
        """Get or create notification preferences for a user."""
        try:
            stmt = select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
            result = await db.execute(stmt)
            prefs = result.scalar_one_or_none()

            if not prefs:
                # Create default preferences
                prefs = NotificationPreference(user_id=user_id)
                db.add(prefs)
                await db.commit()
                await db.refresh(prefs)

            return prefs
        except Exception as e:
            logger.error(f"Failed to get notification preferences: {str(e)}")
            raise

    @staticmethod
    async def should_send_email(
        db: AsyncSession,
        user_id: UUID,
        notification_type: str,
    ) -> bool:
        """Check if an email should be sent based on user preferences."""
        try:
            prefs = await NotificationService.get_user_preferences(db, user_id)

            # Check if emails are enabled globally
            if not prefs.email_notifications:
                return False

            # Check if this notification type is enabled
            notification_types = prefs.notification_types or {}
            if not notification_types.get(notification_type, True):
                return False

            # Check quiet hours
            if prefs.quiet_hours_enabled and prefs.quiet_hours_start and prefs.quiet_hours_end:
                now = utcnow().time()
                start = datetime.strptime(prefs.quiet_hours_start, "%H:%M").time()
                end = datetime.strptime(prefs.quiet_hours_end, "%H:%M").time()

                if start <= end:
                    # Normal case: 22:00 to 08:00
                    if start <= now <= end:
                        return False
                else:
                    # Wrapping case: 22:00 to 08:00 (across midnight)
                    if now >= start or now <= end:
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to check email preferences: {str(e)}")
            return False
