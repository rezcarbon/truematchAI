"""Durable agent-plan status endpoints.

A plan approved in chat runs in the background (``execute_agent_plan``) and is
resumable across sessions/restarts. These endpoints let a client poll a plan's
live progress and list its own plans — so the user can close the chat and check
back later.
"""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.deps import get_current_user
from app.models.agent_plan import AgentPlan
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/plans", tags=["chat"])


def _serialize(plan: AgentPlan) -> dict:
    steps = plan.steps or []
    return {
        "id": str(plan.id),
        "title": plan.title,
        "status": plan.status,
        "current_step": plan.current_step,
        "steps_total": len(steps),
        "steps_completed": sum(1 for s in steps if s.get("status") == "completed"),
        "session_id": str(plan.session_id) if plan.session_id else None,
        "error": plan.error,
        "steps": [
            {
                "order": s.get("order"),
                "tool": s.get("tool"),
                "description": s.get("description"),
                "status": s.get("status"),
                "result": s.get("result"),
            }
            for s in steps
        ],
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


@router.get("")
async def list_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """List the current user's agent plans, newest first."""
    rows = list(
        (
            await db.scalars(
                select(AgentPlan)
                .where(AgentPlan.user_id == user.id)
                .order_by(AgentPlan.created_at.desc())
                .limit(100)
            )
        ).all()
    )
    return {"items": [_serialize(p) for p in rows], "total": len(rows)}


@router.get("/{plan_id}")
async def get_plan(
    plan_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Live status of a single plan (owner-only)."""
    plan = await db.get(AgentPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return _serialize(plan)


@router.post("/{plan_id}/cancel")
async def cancel_plan(
    plan_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Cancel a plan that hasn't finished. Steps already run are not undone."""
    plan = await db.get(AgentPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if plan.status in ("completed", "failed", "cancelled"):
        return {"id": str(plan.id), "status": plan.status, "noop": True}
    plan.status = "cancelled"
    await db.commit()
    return {"id": str(plan.id), "status": "cancelled"}
