"""Aggregate API v1 router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    agents,
    assessments,
    ats,
    auth,
    bulk_actions,
    cv_analysis,
    decisions,
    dei_analytics,
    files,
    jd_simulation,
    notifications,
    notifications_api,
    positions,
    profile,
    recruiter_metrics,
    training,
    uploads,
    scrapers,
    websocket_api,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(decisions.router, prefix="/decisions", tags=["decisions"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(notifications_api.router)
api_router.include_router(ats.router, prefix="/ats", tags=["ats"])
api_router.include_router(bulk_actions.router, prefix="/ats")
api_router.include_router(recruiter_metrics.router, prefix="/ats")
api_router.include_router(dei_analytics.router, prefix="/ats")
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
# Virtual brain / Training Simulation System (admin-only)
api_router.include_router(training.router, tags=["training"])
# CV analysis and JD simulation
api_router.include_router(cv_analysis.router)
api_router.include_router(jd_simulation.router)
# Autonomous agent control + real-time monitoring (REST + WebSocket)
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
# Job scraping and mass uploads
api_router.include_router(uploads.router)
api_router.include_router(scrapers.router)
# Real-time WebSocket updates
api_router.include_router(websocket_api.router)
