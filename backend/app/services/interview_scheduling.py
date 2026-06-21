"""Deterministic interview auto-scheduling.

Finds the earliest time at which ALL required interviewers are simultaneously
free for the requested duration, using their declared availability
(``InterviewSlot``) minus the times they are already booked by existing
interviews. Pure interval arithmetic — same inputs always yield the same slot,
so the result is auditable and testable offline (no external calendar needed).

The optional external-calendar push lives in ``services.calendar_sync`` and is
gated separately; booking works locally even when no calendar is configured.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.interview import Interview, InterviewSlot, InterviewStatus

Interval = tuple[datetime, datetime]


def _clip(intervals: list[Interval], lo: datetime, hi: datetime) -> list[Interval]:
    out = []
    for s, e in intervals:
        s2, e2 = max(s, lo), min(e, hi)
        if s2 < e2:
            out.append((s2, e2))
    return out


def _merge(intervals: list[Interval]) -> list[Interval]:
    """Sort + coalesce overlapping/adjacent intervals."""
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [ordered[0]]
    for s, e in ordered[1:]:
        ls, le = merged[-1]
        if s <= le:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    return merged


def _intersect(a: list[Interval], b: list[Interval]) -> list[Interval]:
    """Intersection of two sorted interval lists."""
    out: list[Interval] = []
    i = j = 0
    a, b = _merge(a), _merge(b)
    while i < len(a) and j < len(b):
        s = max(a[i][0], b[j][0])
        e = min(a[i][1], b[j][1])
        if s < e:
            out.append((s, e))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def _subtract(intervals: list[Interval], busy: list[Interval]) -> list[Interval]:
    """Remove busy intervals from a free-interval list."""
    busy = _merge(busy)
    out: list[Interval] = []
    for s, e in _merge(intervals):
        cur = s
        for bs, be in busy:
            if be <= cur or bs >= e:
                continue
            if bs > cur:
                out.append((cur, min(bs, e)))
            cur = max(cur, be)
            if cur >= e:
                break
        if cur < e:
            out.append((cur, e))
    return out


async def find_earliest_slot(
    db: AsyncSession,
    interviewer_ids: list,
    duration_minutes: int,
    earliest: datetime,
    latest: datetime,
) -> datetime | None:
    """Earliest start where every interviewer is free for ``duration_minutes``.

    Returns the start datetime, or None when no common slot exists in
    [earliest, latest]. With no interviewers, falls back to ``earliest`` (no
    availability constraint to satisfy).
    """
    duration = timedelta(minutes=duration_minutes)
    if earliest >= latest or duration <= timedelta(0):
        return None
    if not interviewer_ids:
        return earliest

    # Per-interviewer availability (available=True), clipped to the window.
    common: list[Interval] | None = None
    for iid in interviewer_ids:
        rows = (
            await db.scalars(
                select(InterviewSlot).where(
                    InterviewSlot.interviewer_id == iid,
                    InterviewSlot.available.is_(True),
                    InterviewSlot.end_time > earliest,
                    InterviewSlot.start_time < latest,
                )
            )
        ).all()
        free = _clip([(s.start_time, s.end_time) for s in rows], earliest, latest)
        if not free:
            return None  # this interviewer has no availability → no common slot
        common = free if common is None else _intersect(common, free)
        if not common:
            return None

    # Remove times any of these interviewers is already booked.
    booked = (
        await db.scalars(
            select(Interview).where(
                Interview.scheduled_at.is_not(None),
                Interview.status == InterviewStatus.scheduled,
            )
        )
    ).all()
    busy: list[Interval] = []
    idset = {str(i) for i in interviewer_ids}
    for iv in booked:
        if not iv.scheduled_at:
            continue
        if idset & {str(x) for x in (iv.interviewer_ids or [])}:
            busy.append(
                (iv.scheduled_at, iv.scheduled_at + timedelta(minutes=settings.interview_default_minutes))
            )

    free_after_busy = _subtract(common or [], busy)
    for s, e in sorted(free_after_busy):
        if e - s >= duration:
            return s
    return None
