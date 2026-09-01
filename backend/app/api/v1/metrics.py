"""Metrics and analytics endpoints for monitoring system health (admin-only)."""
import logging
from typing import Optional

from fastapi import APIRouter

from app.deps import CurrentAdmin, DBSession
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics")
async def get_system_metrics(admin: CurrentAdmin, db: DBSession, days: int = 7) -> dict:
    """System health and metrics (admin only)."""
    session_metrics = await AnalyticsService.get_session_metrics(days=days, db=db)
    message_metrics = await AnalyticsService.get_message_metrics(days=days, db=db)
    governance_metrics = await AnalyticsService.get_governance_metrics(days=days, db=db)
    user_metrics = await AnalyticsService.get_user_metrics(days=days, db=db)
    system_health = await AnalyticsService.get_system_health(db=db)
    return {
        "status": "success",
        "data": {
            "system_health": system_health,
            "sessions": session_metrics,
            "messages": message_metrics,
            "governance": governance_metrics,
            "users": user_metrics,
        },
    }


@router.get("/metrics/sessions")
async def get_session_metrics(
    admin: CurrentAdmin, db: DBSession, user_id: Optional[str] = None, days: int = 7
) -> dict:
    return {"status": "success", "data": await AnalyticsService.get_session_metrics(user_id=user_id, days=days, db=db)}


@router.get("/metrics/messages")
async def get_message_metrics(
    admin: CurrentAdmin, db: DBSession, user_id: Optional[str] = None, days: int = 7
) -> dict:
    return {"status": "success", "data": await AnalyticsService.get_message_metrics(user_id=user_id, days=days, db=db)}


@router.get("/metrics/governance")
async def get_governance_metrics(admin: CurrentAdmin, db: DBSession, days: int = 7) -> dict:
    return {"status": "success", "data": await AnalyticsService.get_governance_metrics(days=days, db=db)}


@router.get("/metrics/users")
async def get_user_metrics(admin: CurrentAdmin, db: DBSession, days: int = 7) -> dict:
    return {"status": "success", "data": await AnalyticsService.get_user_metrics(days=days, db=db)}
