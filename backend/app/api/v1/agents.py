"""Agent control & monitoring API.

These endpoints give recruiters, admins, and the iOS app live visibility into
the autonomous agents and the ability to command them from anywhere.

  GET  /agents/queue              — current ingest queue (all items)
  GET  /agents/queue/{id}         — single item detail
  POST /agents/queue/{id}/approve — advance an awaiting_review item
  POST /agents/queue/{id}/reject  — reject and stop an item
  POST /agents/queue/{id}/reassign — reassign a CV to a different position
  GET  /agents/status/quick       — quick agent health dashboard
  GET  /agents/queue?awaiting_review=true — filtered queue with decision deadline
  POST /agents/trigger            — manually trigger CV assessment (iOS on-the-go)
  POST /agents/jd/draft           — submit a JD draft for autonomous analysis
  GET  /agents/jd/{position_id}/suggestions — fetch the AI-improved JD draft

WebSocket:
  WS   /ws/agents                 — real-time queue update feed (JSON events)
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy import select, func

from app.deps import CurrentUser, DBSession
from app.models.ingest_queue import IngestQueueItem, IngestStatus
from app.models.position import Position
from app.models.resume import Resume
from app.schemas.agents import (
    AgentStatusResponse,
    AgentsStatusResponse,
    QueueItemDetail as QueueItemDetailSchema,
)
from app.websocket.agents_operator import get_operator_manager

router = APIRouter()
logger = logging.getLogger("truematch.agents_api")


# ── Schemas ──────────────────────────────────────────────────────────────────

class QueueItemSummary(BaseModel):
    id: uuid.UUID
    source: str
    ingest_type: str
    status: str
    resume_id: uuid.UUID | None
    assessment_id: uuid.UUID | None
    position_id: uuid.UUID | None
    retry_count: int
    created_at: str


class QueueItemDetail(QueueItemSummary):
    source_ref: str | None
    last_error: str | None
    jd_agent_output: dict | None
    review_notes: str | None


class ApprovePayload(BaseModel):
    notes: str | None = None


class ReassignPayload(BaseModel):
    position_id: uuid.UUID
    notes: str | None = None


class TriggerPayload(BaseModel):
    resume_id: uuid.UUID
    position_id: uuid.UUID | None = None
    jd_text: str | None = None


class JDDraftPayload(BaseModel):
    jd_text: str
    position_id: uuid.UUID | None = None
    title: str | None = None


# ── Queue endpoints ───────────────────────────────────────────────────────────

@router.get("/queue", response_model=list[QueueItemSummary])
async def list_queue(
    user: CurrentUser,
    db: DBSession,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
) -> list[QueueItemSummary]:
    """All ingest queue items (newest first). Optionally filter by status."""
    stmt = select(IngestQueueItem).order_by(IngestQueueItem.created_at.desc()).limit(limit)
    if status_filter:
        stmt = stmt.where(IngestQueueItem.status == status_filter)
    items = list((await db.scalars(stmt)).all())
    return [_summary(i) for i in items]


@router.get("/queue/{item_id}", response_model=QueueItemDetail)
async def get_queue_item(item_id: uuid.UUID, user: CurrentUser, db: DBSession) -> QueueItemDetail:
    item = await db.get(IngestQueueItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return _detail(item)


@router.post("/queue/{item_id}/approve")
async def approve_item(
    item_id: uuid.UUID, payload: ApprovePayload, user: CurrentUser, db: DBSession
) -> dict:
    """Approve an awaiting_review item — enqueues the assessment pipeline."""
    item = await _get_actionable(item_id, db)
    if item.status != IngestStatus.awaiting_review:
        raise HTTPException(status_code=409, detail=f"Item is {item.status}, not awaiting_review")
    item.reviewed_by = user.id
    item.review_notes = payload.notes
    item.status = IngestStatus.processing
    await db.flush()

    assessment_id = None

    # If it's a CV item with a resume and position, kick off the pipeline.
    if item.ingest_type == "cv" and item.resume_id and item.position_id:
        from app.models.assessment import Assessment
        assessment = Assessment(
            resume_id=item.resume_id, position_id=item.position_id, user_id=user.id
        )
        db.add(assessment)
        await db.flush()
        item.assessment_id = assessment.id
        assessment_id = assessment.id
        from app.workers.tasks import run_assessment
        run_assessment.delay(str(assessment.id))

    # Broadcast to operator dashboard via WebSocket
    await _broadcast_event(
        event_type="queue_item_action",
        item_id=item_id,
        action="approved",
        user_id=user.id,
        status="processing",
        notes=payload.notes,
        assessment_id=assessment_id,
    )

    await _broadcast({"event": "item_approved", "id": str(item_id), "status": "processing"})
    return {"status": "approved", "id": str(item_id)}


@router.post("/queue/{item_id}/reject")
async def reject_item(
    item_id: uuid.UUID, payload: ApprovePayload, user: CurrentUser, db: DBSession
) -> dict:
    """Reject an item — prevents it from entering the assessment pipeline."""
    item = await _get_actionable(item_id, db)
    item.status = IngestStatus.rejected
    item.reviewed_by = user.id
    item.review_notes = payload.notes
    await db.flush()

    # Broadcast to operator dashboard via WebSocket
    await _broadcast_event(
        event_type="queue_item_action",
        item_id=item_id,
        action="rejected",
        user_id=user.id,
        status="rejected",
        notes=payload.notes,
    )

    await _broadcast({"event": "item_rejected", "id": str(item_id)})
    return {"status": "rejected", "id": str(item_id)}


@router.post("/queue/{item_id}/reassign")
async def reassign_item(
    item_id: uuid.UUID, payload: ReassignPayload, user: CurrentUser, db: DBSession
) -> dict:
    """Reassign a CV to a different open position, then approve."""
    item = await _get_actionable(item_id, db)
    position = await db.get(Position, payload.position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    item.position_id = payload.position_id
    item.review_notes = payload.notes
    # Re-use the approve path.
    item.status = IngestStatus.awaiting_review
    await db.flush()
    return await approve_item(item_id, ApprovePayload(notes=payload.notes), user, db)


# ── Manual trigger ────────────────────────────────────────────────────────────

@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_assessment(
    payload: TriggerPayload, user: CurrentUser, db: DBSession
) -> dict:
    """Manually trigger an assessment from iOS (resume + position or JD text).
    Returns immediately
    processing is async via the worker."""
    resume = await db.get(Resume, payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    position_id = payload.position_id
    # If no position_id but JD text is provided, create a self-assessment position.
    if position_id is None and payload.jd_text:
        from app.engines.intake import analyze_jd
        from app.engines import reasoning
        from app.models.position import PositionStatus
        requirements = analyze_jd(payload.jd_text or "")
        review = reasoning.interrogate_jd(payload.jd_text or "")
        pos = Position(
            company_id=None, created_by=user.id,
            title="iOS triggered assessment",
            description=payload.jd_text,
            parsed_requirements=requirements,
            jd_quality_score=review.get("quality_score"),
            jd_issues={"issues": review.get("issues", [])},
            status=PositionStatus.open,
        )
        db.add(pos)
        await db.flush()
        position_id = pos.id

    if position_id is None:
        raise HTTPException(status_code=422, detail="position_id or jd_text required")

    from app.models.assessment import Assessment
    assessment = Assessment(
        resume_id=payload.resume_id, position_id=position_id, user_id=user.id
    )
    db.add(assessment)
    await db.flush()
    from app.workers.tasks import run_assessment
    run_assessment.delay(str(assessment.id))
    return {"assessment_id": str(assessment.id), "status": "queued"}


# ── JD draft submission ───────────────────────────────────────────────────────

@router.post("/jd/draft", status_code=status.HTTP_202_ACCEPTED)
async def submit_jd_draft(
    payload: JDDraftPayload, user: CurrentUser, db: DBSession
) -> dict:
    """Submit a JD draft for autonomous quality review. Returns a queue item id."""
    if not payload.jd_text or len(payload.jd_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="jd_text too short")
    from app.workers.agents.ingest_jd import process_draft
    pos_str = str(payload.position_id) if payload.position_id else None
    task = process_draft.delay(payload.jd_text, pos_str, payload.title)
    return {"task_id": task.id, "status": "queued"}


@router.get("/jd/{position_id}/suggestions")
async def get_jd_suggestions(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    """Fetch the latest AI-improved JD draft + quality analysis for a position."""
    stmt = (
        select(IngestQueueItem)
        .where(
            IngestQueueItem.position_id == position_id,
            IngestQueueItem.ingest_type == "jd_draft",
        )
        .order_by(IngestQueueItem.created_at.desc())
        .limit(1)
    )
    item = await db.scalar(stmt)
    if item is None:
        raise HTTPException(status_code=404, detail="No JD draft analysis found for this position")
    return {
        "position_id": str(position_id),
        "status": item.status,
        "jd_improved_draft": item.jd_improved_draft,
        "jd_agent_output": item.jd_agent_output,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


# ── Agent health & metrics ───────────────────────────────────────────────────

@router.get("/status/quick", response_model=AgentsStatusResponse)
async def get_quick_status(user: CurrentUser, db: DBSession) -> AgentsStatusResponse:
    """
    Quick agent health dashboard.

    Returns:
        AgentsStatusResponse with CV, JD, and Email agent status summaries.
    """
    now = datetime.utcnow()
    hours_24_ago = now - timedelta(hours=24)

    async def get_agent_status(ingest_type: str) -> AgentStatusResponse:
        """Get status for a specific agent type."""
        # Count items in queue
        queue_count = await db.scalar(
            select(func.count(IngestQueueItem.id)).where(
                IngestQueueItem.ingest_type == ingest_type,
                IngestQueueItem.status.in_([
                    IngestStatus.pending,
                    IngestStatus.extracting,
                    IngestStatus.matching,
                    IngestStatus.awaiting_review,
                ]),
            )
        )

        # Count processed in last 24 hours
        processed_24h = await db.scalar(
            select(func.count(IngestQueueItem.id)).where(
                IngestQueueItem.ingest_type == ingest_type,
                IngestQueueItem.status == IngestStatus.completed,
                IngestQueueItem.updated_at >= hours_24_ago,
            )
        )

        # Count failed in last 24 hours
        failed_24h = await db.scalar(
            select(func.count(IngestQueueItem.id)).where(
                IngestQueueItem.ingest_type == ingest_type,
                IngestQueueItem.status == IngestStatus.failed,
                IngestQueueItem.updated_at >= hours_24_ago,
            )
        )

        # Get last activity
        last_item = await db.scalar(
            select(IngestQueueItem.updated_at)
            .where(IngestQueueItem.ingest_type == ingest_type)
            .order_by(IngestQueueItem.updated_at.desc())
            .limit(1)
        )

        return AgentStatusResponse(
            agent_type=ingest_type,
            running=queue_count > 0 or processed_24h > 0,
            queue_size=queue_count or 0,
            processed_24h=processed_24h or 0,
            failed_24h=failed_24h or 0,
            avg_processing_time_seconds=None,  # Would need processing_started_at timestamp
            last_activity_at=last_item,
        )

    cv_status = await get_agent_status("cv")
    jd_status = await get_agent_status("jd_draft")
    # Email agent would use a different model; for now, create a placeholder
    email_status = AgentStatusResponse(
        agent_type="email",
        running=False,
        queue_size=0,
        processed_24h=0,
        failed_24h=0,
    )

    return AgentsStatusResponse(
        cv=cv_status,
        jd=jd_status,
        email=email_status,
        timestamp=now,
    )


@router.get("/queue", response_model=list[QueueItemDetailSchema])
async def list_queue(
    user: CurrentUser,
    db: DBSession,
    status_filter: str | None = Query(None, alias="status"),
    awaiting_review: bool = Query(False, description="Filter to awaiting_review items only"),
    sort: str = Query("created_at", description="Sort by: created_at, updated_at, retry_count"),
    limit: int = Query(50, ge=1, le=200),
) -> list[QueueItemDetailSchema]:
    """
    Get ingest queue items with optional filtering.

    Args:
        status_filter: Filter by status (e.g., 'pending', 'processing')
        awaiting_review: If True, only return items awaiting human review
        sort: Sort field (created_at, updated_at, retry_count)
        limit: Maximum items to return

    Returns:
        List of queue items with decision support fields.
    """
    stmt = select(IngestQueueItem)

    if awaiting_review:
        stmt = stmt.where(IngestQueueItem.status == IngestStatus.awaiting_review)
    elif status_filter:
        stmt = stmt.where(IngestQueueItem.status == status_filter)

    # Apply sorting
    if sort == "updated_at":
        stmt = stmt.order_by(IngestQueueItem.updated_at.desc())
    elif sort == "retry_count":
        stmt = stmt.order_by(IngestQueueItem.retry_count.desc())
    else:
        stmt = stmt.order_by(IngestQueueItem.created_at.desc())

    stmt = stmt.limit(limit)
    items = list((await db.scalars(stmt)).all())

    return [_to_detail_schema(item) for item in items]


# ── WebSocket real-time feed ──────────────────────────────────────────────────

_connections: set[WebSocket] = set()


async def _broadcast(payload: dict) -> None:
    """Push a JSON event to every connected WebSocket client."""
    msg = json.dumps(payload)
    dead: set[WebSocket] = set()
    for ws in _connections:
        try:
            await ws.send_text(msg)
        except Exception:  # noqa: BLE001
            dead.add(ws)
    _connections.difference_update(dead)


@router.websocket("/ws")
async def agents_ws(websocket: WebSocket) -> None:
    """Real-time agent event stream — connect once and receive JSON push events."""
    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            # Keep alive — clients can send pings; we echo pong.
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            if data.strip() == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        _connections.discard(websocket)


@router.websocket("/ws/operator")
async def operator_ws(websocket: WebSocket) -> None:
    """
    Operator dashboard feed — real-time queue item actions and agent alerts.

    Receives events like:
    - queue_item_action: when items are approved/rejected/reassigned
    - agent_status_change: when agent status changes
    - processing_alert: errors, warnings from agents
    """
    manager = get_operator_manager()
    await manager.subscribe(websocket)
    try:
        while True:
            # Keep connection alive; clients can send pings
            data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            if data.strip() == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        await manager.unsubscribe(websocket)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_actionable(item_id: uuid.UUID, db: DBSession) -> IngestQueueItem:
    item = await db.get(IngestQueueItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if item.status in (IngestStatus.completed, IngestStatus.failed, IngestStatus.rejected):
        raise HTTPException(status_code=409, detail=f"Item already in terminal state: {item.status}")
    return item


def _summary(i: IngestQueueItem) -> QueueItemSummary:
    return QueueItemSummary(
        id=i.id, source=i.source, ingest_type=i.ingest_type, status=i.status,
        resume_id=i.resume_id, assessment_id=i.assessment_id, position_id=i.position_id,
        retry_count=i.retry_count, created_at=i.created_at.isoformat() if i.created_at else "",
    )


def _detail(i: IngestQueueItem) -> QueueItemDetail:
    return QueueItemDetail(
        **_summary(i).__dict__,
        source_ref=i.source_ref,
        last_error=i.last_error,
        jd_agent_output=i.jd_agent_output,
        review_notes=i.review_notes,
    )


def _to_detail_schema(item: IngestQueueItem) -> QueueItemDetailSchema:
    """Convert an IngestQueueItem to QueueItemDetailSchema with decision support fields."""
    sender_name = None
    if item.sender_meta and isinstance(item.sender_meta, dict):
        sender_name = item.sender_meta.get("name") or item.sender_meta.get("sender_name")

    return QueueItemDetailSchema(
        id=item.id,
        source=item.source,
        ingest_type=item.ingest_type,
        status=item.status,
        created_at=item.created_at.isoformat() if item.created_at else "",
        resume_id=item.resume_id,
        assessment_id=item.assessment_id,
        position_id=item.position_id,
        retry_count=item.retry_count,
        source_ref=item.source_ref,
        last_error=item.last_error,
        jd_agent_output=item.jd_agent_output,
        awaiting_review=item.status == IngestStatus.awaiting_review,
        decision_deadline=None,  # Would be set based on business rules
        notes_history=[item.review_notes] if item.review_notes else [],
        sender_name=sender_name,
        review_notes=item.review_notes,
    )


async def _broadcast_event(
    event_type: str,
    item_id: uuid.UUID,
    action: str,
    user_id: uuid.UUID,
    status: str,
    notes: str | None = None,
    assessment_id: uuid.UUID | None = None,
) -> None:
    """
    Broadcast a queue item action event to all connected operators.

    Args:
        event_type: Type of event (e.g., 'queue_item_action')
        item_id: ID of the queue item
        action: Action performed ('approved', 'rejected', 'reassigned')
        user_id: ID of user performing the action
        status: New status of the item
        notes: Optional review notes
        assessment_id: Optional assessment ID created by the action
    """
    manager = get_operator_manager()
    await manager.broadcast_queue_item_action(
        item_id=str(item_id),
        action=action,
        user_id=str(user_id),
        status=status,
        notes=notes,
        assessment_id=str(assessment_id) if assessment_id else None,
    )
