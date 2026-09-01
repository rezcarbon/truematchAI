"""Analytics and metrics tracking for the TrueMatch system."""
import logging
from datetime import timedelta
from app.core.clock import utcnow
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.models.governance_review import GovernanceReview

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Track and report system metrics and user engagement."""

    @staticmethod
    async def get_session_metrics(
        user_id: Optional[str] = None,
        days: int = 7,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Get conversation session metrics.

        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            db: Database session

        Returns:
            Dict with session metrics
        """
        if not db:
            return {}

        try:
            cutoff_date = utcnow() - timedelta(days=days)

            # Build base query
            stmt = select(func.count(ChatSession.id)).where(
                ChatSession.created_at >= cutoff_date
            )

            if user_id:
                stmt = stmt.where(ChatSession.user_id == user_id)

            result = await db.execute(stmt)
            total_sessions = result.scalar() or 0

            # Average duration
            stmt = select(func.avg(ChatSession.updated_at - ChatSession.created_at)).where(
                ChatSession.created_at >= cutoff_date
            )
            if user_id:
                stmt = stmt.where(ChatSession.user_id == user_id)

            result = await db.execute(stmt)
            avg_duration = result.scalar()

            return {
                "total_sessions": total_sessions,
                "avg_session_duration": str(avg_duration) if avg_duration else None,
                "period_days": days,
            }
        except Exception as e:
            logger.error(f"Failed to get session metrics: {e}")
            return {}

    @staticmethod
    async def get_message_metrics(
        user_id: Optional[str] = None,
        days: int = 7,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Get message and engagement metrics.

        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            db: Database session

        Returns:
            Dict with message metrics
        """
        if not db:
            return {}

        try:
            cutoff_date = utcnow() - timedelta(days=days)

            # Total messages
            stmt = select(func.count(ChatMessage.id)).where(ChatMessage.created_at >= cutoff_date)
            if user_id:
                stmt = stmt.join(ChatSession).where(ChatSession.user_id == user_id)

            result = await db.execute(stmt)
            total_messages = result.scalar() or 0

            # User messages vs assistant messages
            stmt = (
                select(ChatMessage.role, func.count(ChatMessage.id))
                .where(ChatMessage.created_at >= cutoff_date)
                .group_by(ChatMessage.role)
            )
            if user_id:
                stmt = stmt.join(ChatSession).where(ChatSession.user_id == user_id)

            result = await db.execute(stmt)
            role_counts = {row[0]: row[1] for row in result.all()}

            return {
                "total_messages": total_messages,
                "user_messages": role_counts.get("user", 0),
                "assistant_messages": role_counts.get("assistant", 0),
                "avg_messages_per_session": (
                    total_messages // max(1, result.scalar() or 1) if total_messages else 0
                ),
            }
        except Exception as e:
            logger.error(f"Failed to get message metrics: {e}")
            return {}

    @staticmethod
    async def get_governance_metrics(
        days: int = 7,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Get governance review metrics.

        Args:
            days: Number of days to look back
            db: Database session

        Returns:
            Dict with governance metrics
        """
        if not db:
            return {}

        try:
            cutoff_date = utcnow() - timedelta(days=days)

            # Count by status
            stmt = (
                select(GovernanceReview.status, func.count(GovernanceReview.id))
                .where(GovernanceReview.created_at >= cutoff_date)
                .group_by(GovernanceReview.status)
            )

            result = await db.execute(stmt)
            status_counts = {row[0]: row[1] for row in result.all()}

            return {
                "pending": status_counts.get("pending", 0),
                "approved": status_counts.get("approved", 0),
                "rejected": status_counts.get("rejected", 0),
                "escalated": status_counts.get("escalated", 0),
                "total": sum(status_counts.values()),
            }
        except Exception as e:
            logger.error(f"Failed to get governance metrics: {e}")
            return {}

    @staticmethod
    async def get_user_metrics(
        days: int = 7,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Get user and engagement metrics.

        Args:
            days: Number of days to look back
            db: Database session

        Returns:
            Dict with user metrics
        """
        if not db:
            return {}

        try:
            # Total active users (with sessions in period)
            cutoff_date = utcnow() - timedelta(days=days)
            stmt = select(func.count(func.distinct(ChatSession.user_id))).where(
                ChatSession.created_at >= cutoff_date
            )

            result = await db.execute(stmt)
            active_users = result.scalar() or 0

            # Users by role
            stmt = (
                select(User.role, func.count(func.distinct(ChatSession.user_id)))
                .select_from(ChatSession)
                .join(User)
                .where(ChatSession.created_at >= cutoff_date)
                .group_by(User.role)
            )

            result = await db.execute(stmt)
            role_counts = {row[0]: row[1] for row in result.all()}

            return {
                "active_users": active_users,
                "by_role": {
                    "admin": role_counts.get("admin", 0),
                    "recruiter": role_counts.get("recruiter", 0),
                    "candidate": role_counts.get("candidate", 0),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get user metrics: {e}")
            return {}

    @staticmethod
    async def get_system_health(db: Optional[AsyncSession] = None) -> dict:
        """Get overall system health metrics.

        Args:
            db: Database session

        Returns:
            Dict with system health indicators
        """
        if not db:
            return {}

        try:
            # Get metrics for different time windows
            metrics_24h = await AnalyticsService.get_session_metrics(
                days=1, db=db
            )
            metrics_7d = await AnalyticsService.get_session_metrics(
                days=7, db=db
            )
            governance = await AnalyticsService.get_governance_metrics(days=1, db=db)

            return {
                "status": "healthy",
                "last_24_hours": metrics_24h,
                "last_7_days": metrics_7d,
                "governance": governance,
                "timestamp": utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {"status": "degraded", "error": str(e)}
