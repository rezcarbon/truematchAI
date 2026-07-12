"""Aggregate API v1 router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    admin_console,
    agent_plans,
    agents,
    applications,
    assessments,
    ats,
    auth,
    billing,
    bulk_actions,
    career_coach,
    chat,
    chat_actions,
    chat_streaming,
    capability_translation,
    transition_intelligence,
    compliance,
    connectors,
    cv_analysis,
    decisions,
    dei_analytics,
    files,
    governance_reviews,
    jd_simulation,
    # job_search,  # Temporarily disabled due to schema import issues
    metrics,
    notifications,
    notifications_api,
    positions,
    profile,
    realtime_progress_api,
    recruiter_metrics,
    resume_versioning,
    training,
    training_data,
    uploads,
    scrapers,
    websocket_api,
)
from app.api.v1.admin import autonomous

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
# NOTE: admin_console.py was previously named admin.py, which the app/api/v1/admin/
# PACKAGE silently shadowed — its endpoints (audit, compliance report, governance
# config, analytics) were never mounted, and the autonomous router got mounted
# twice (/admin/admin/autonomous/*). Renamed to fix both.
api_router.include_router(admin_console.router, prefix="/admin", tags=["admin"])
api_router.include_router(autonomous.router, tags=["admin", "autonomous"])  # Autonomous operation control
api_router.include_router(metrics.router, tags=["admin", "metrics"])  # System metrics and analytics
# Virtual brain / Training Simulation System (admin-only)
api_router.include_router(training.router, tags=["training"])
api_router.include_router(training_data.router)  # Training data upload & chat
# Conversational AI interface
api_router.include_router(chat.router)
api_router.include_router(chat_streaming.router)  # SSE streaming for real-time progress
api_router.include_router(chat_actions.router)  # Action confirmation and execution
api_router.include_router(agent_plans.router)  # Durable agent-plan status
api_router.include_router(connectors.router)  # External ATS connectors
api_router.include_router(billing.router)  # Billing & payments (Stripe)
# CV analysis and JD simulation
api_router.include_router(cv_analysis.router)
api_router.include_router(capability_translation.router)
api_router.include_router(transition_intelligence.router)
api_router.include_router(jd_simulation.router)
# Governance reviews and compliance
api_router.include_router(governance_reviews.router)
# Autonomous agent control + real-time monitoring (REST + WebSocket)
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
# Job scraping and mass uploads
api_router.include_router(uploads.router)
api_router.include_router(scrapers.router)
# Real-time WebSocket updates
api_router.include_router(websocket_api.router)
# Phase C+D: Provenance, Audit Trail, Reproducibility, Learning Integration
api_router.include_router(compliance.router)
# Phase E: IDF Corpus Learning & Real-Time Progress
api_router.include_router(realtime_progress_api.router)
# Candidate features: Resume versioning, Job search, Applications, Career coaching
api_router.include_router(resume_versioning.router)
# api_router.include_router(job_search.router)  # Temporarily disabled due to schema import issues
api_router.include_router(applications.router)
api_router.include_router(career_coach.router)
