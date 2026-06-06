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
        "app.workers.agents.ingest_cv",
        "app.workers.agents.ingest_jd",
        "app.workers.cv_analysis",
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
    },
)
