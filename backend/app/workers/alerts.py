"""Proactive alert tasks — the agent reaching out, not just reacting.

Periodic Celery Beat tasks that query pipeline state and push notifications via
the existing NotificationService, turning a reactive notification system into a
proactive one:

- `check_stale_candidates` — candidates sitting in a non-terminal stage past a
  threshold get surfaced to the owning recruiter.
- `daily_digest` — a once-a-day per-recruiter summary of their active pipeline
  and items awaiting review.

Both are idempotent per day (idempotency_key includes the date) so re-runs don't
spam. They run an async body on a fresh async session (the worker is sync).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.application import Application
from app.models.ingest_queue import IngestQueueItem
from app.models.position import Position
from app.models.user import User, UserRole
from app.services.notification_service import NotificationService
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.alerts")

# Stages a candidate can sit in without being a final outcome.
_ACTIVE_STAGES = ["applied", "phone_screen", "technical", "onsite", "offer"]
_STALE_DAYS = 7


def _async_factory():
    engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
    return engine, async_sessionmaker(bind=engine, expire_on_commit=False)


def _today() -> str:
    # date-only key so an alert fires at most once per recruiter per day
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def _check_stale_candidates() -> dict:
    engine, factory = _async_factory()
    sent = 0
    try:
        async with factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=_STALE_DAYS)
            # Count stale applications per owning recruiter (Position.created_by).
            stmt = (
                select(Position.created_by, func.count(Application.id))
                .join(Application, Application.position_id == Position.id)
                .where(
                    Application.stage.in_(_ACTIVE_STAGES),
                    Application.stage_entered_at < cutoff,
                    Position.created_by.is_not(None),
                )
                .group_by(Position.created_by)
            )
            for recruiter_id, count in (await db.execute(stmt)).all():
                if not recruiter_id or count == 0:
                    continue
                await NotificationService.create_notification(
                    db=db,
                    user_id=recruiter_id,
                    notification_type="pipeline_update",
                    title="Candidates need attention",
                    message=(
                        f"{count} candidate(s) have been in the same pipeline stage "
                        f"for over {_STALE_DAYS} days. Review or advance them."
                    ),
                    action_url="/recruiter/pipeline",
                    idempotency_key=f"stale-{recruiter_id}-{_today()}",
                )
                sent += 1
            await db.commit()
    finally:
        await engine.dispose()
    logger.info("Stale-candidate alerts sent", extra={"recruiters_notified": sent})
    return {"recruiters_notified": sent}


async def _daily_digest() -> dict:
    engine, factory = _async_factory()
    sent = 0
    try:
        async with factory() as db:
            recruiters = (
                await db.execute(select(User).where(User.role == UserRole.recruiter))
            ).scalars().all()
            for r in recruiters:
                active = (
                    await db.execute(
                        select(func.count(Application.id))
                        .join(Position, Application.position_id == Position.id)
                        .where(
                            Position.created_by == r.id,
                            Application.stage.in_(_ACTIVE_STAGES),
                        )
                    )
                ).scalar() or 0
                awaiting = (
                    await db.execute(
                        select(func.count(IngestQueueItem.id)).where(
                            IngestQueueItem.status == "awaiting_review"
                        )
                    )
                ).scalar() or 0
                if active == 0 and awaiting == 0:
                    continue
                await NotificationService.create_notification(
                    db=db,
                    user_id=r.id,
                    notification_type="system_alert",
                    title="Your daily hiring digest",
                    message=(
                        f"{active} candidate(s) active in your pipeline · "
                        f"{awaiting} item(s) awaiting review."
                    ),
                    action_url="/recruiter/dashboard",
                    idempotency_key=f"digest-{r.id}-{_today()}",
                )
                sent += 1
            await db.commit()
    finally:
        await engine.dispose()
    logger.info("Daily digests sent", extra={"recruiters_notified": sent})
    return {"recruiters_notified": sent}


@celery_app.task(name="app.workers.alerts.check_stale_candidates")
def check_stale_candidates() -> dict:
    return asyncio.run(_check_stale_candidates())


@celery_app.task(name="app.workers.alerts.daily_digest")
def daily_digest() -> dict:
    return asyncio.run(_daily_digest())
