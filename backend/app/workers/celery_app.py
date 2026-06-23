"""Celery application instance."""
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "truematch",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks",
        "app.workers.retention",
        "app.workers.agents.ingest_cv",
        "app.workers.agents.ingest_jd",
        "app.workers.agents.ingest_drive",
        "app.workers.cv_analysis",
        "app.workers.capability_translation",
        "app.workers.transition_intelligence",
        "app.workers.jd_simulation",
        "app.workers.alerts",
        "app.workers.dlq",
        "app.workers.user_memory",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    # Don't double-run a long LLM pipeline if a worker dies mid-task.
    task_reject_on_worker_lost=False,
    worker_prefetch_multiplier=1,
    # Bound runaway tasks: soft limit raises in-task for cleanup, hard limit kills.
    task_soft_time_limit=600,  # 10 min
    task_time_limit=660,  # 11 min hard kill
    result_expires=86400,  # results TTL 24h
    timezone="UTC",
    enable_utc=True,
    # --- Celery Beat — autonomous agent polling schedule ---
    # Agents are safe to overlap: each run locks a set of items by updating
    # status before processing, so concurrent beats can't double-process.
    beat_schedule={
        "poll-cv-folder": {
            "task": "app.workers.agents.ingest_cv.poll_folder",
            "schedule": settings.ingest_folder_poll_seconds,
        },
        "poll-jd-folder": {
            "task": "app.workers.agents.ingest_jd.poll_folder",
            "schedule": settings.ingest_folder_poll_seconds,
        },
        "poll-cv-email": {
            "task": "app.workers.agents.ingest_cv.poll_email",
            "schedule": settings.ingest_email_poll_seconds,
        },
        "poll-drive": {
            "task": "app.workers.agents.ingest_drive.poll_drive",
            "schedule": settings.drive_ingest_poll_seconds,
        },
        "retention-daily-sweep": {
            "task": "app.workers.retention.retention_daily_sweep",
            "schedule": 86400,  # Every 24 hours
            "options": {
                "expires": 3600,  # Task expires after 1 hour if not executed
            },
        },
        # --- Proactive alerts (intelligence-driven, not intake-driven) ---
        "check-stale-candidates": {
            "task": "app.workers.alerts.check_stale_candidates",
            "schedule": 21600,  # Every 6 hours
            "options": {"expires": 3600},
        },
        "daily-digest": {
            "task": "app.workers.alerts.daily_digest",
            "schedule": 86400,  # Once a day
            "options": {"expires": 3600},
        },
        # --- Durable user memory: merge fresh chat activity hourly ---
        "merge-user-memories": {
            "task": "app.workers.user_memory.merge_stale_user_memories",
            "schedule": 3600,
            "options": {"expires": 1800},
        },
        # --- Self-learned role taxonomy: re-cluster JDs every 6h ---
        "rebuild-role-taxonomy": {
            "task": "app.workers.tasks.rebuild_role_taxonomy",
            "schedule": 21600,
            "options": {"expires": 3600},
        },
        # --- Durable agent plans: re-enqueue any stalled background plan ---
        "resume-stalled-plans": {
            "task": "app.workers.tasks.resume_stalled_plans",
            "schedule": 120,
            "options": {"expires": 110},
        },
        # --- Phase 3: re-assess tracked transitions whose quarterly review is due.
        # Sweeps daily; each analysis only re-runs when its own next_review_at lapses.
        "reassess-due-transitions": {
            "task": "app.workers.transition_intelligence.reassess_due_transitions",
            "schedule": 86400,  # daily sweep
            "options": {"expires": 43200},
        },
    },
)
