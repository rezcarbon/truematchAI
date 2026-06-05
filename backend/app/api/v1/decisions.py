"""Decision endpoints — recruiter actions on assessments."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DBSession
from app.models.assessment import Assessment
from app.models.audit import AuditTrail
from app.models.decision import Decision
from app.models.user import UserRole
from app.schemas.decision import DecisionCreate, DecisionResponse

router = APIRouter()


def _require_recruiter(user: CurrentUser) -> None:
    if user.role not in (UserRole.recruiter, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter role required"
        )


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    payload: DecisionCreate, user: CurrentUser, db: DBSession
) -> Decision:
    _require_recruiter(user)
    assessment = await db.get(Assessment, payload.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    decision = Decision(
        assessment_id=payload.assessment_id,
        position_id=payload.position_id,
        recruiter_id=user.id,
        decision=payload.decision,
        ai_recommendation_followed=payload.ai_recommendation_followed,
        override_reasoning=payload.override_reasoning,
        cultural_fit_notes=payload.cultural_fit_notes,
        interview_notes=payload.interview_notes,
    )
    db.add(decision)
    await db.flush()

    db.add(
        AuditTrail(
            assessment_id=payload.assessment_id,
            event_type="decision.recorded",
            event_data={
                "decision": payload.decision.value,
                "ai_recommendation_followed": payload.ai_recommendation_followed,
            },
            actor_id=user.id,
            actor_type="recruiter",
        )
    )
    await db.flush()
    return decision


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> Decision:
    _require_recruiter(user)
    decision = await db.get(Decision, decision_id)
    if decision is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return decision


@router.get("", response_model=list[DecisionResponse])
async def list_decisions(
    user: CurrentUser,
    db: DBSession,
    assessment_id: uuid.UUID | None = None,
    position_id: uuid.UUID | None = None,
) -> list[Decision]:
    _require_recruiter(user)
    stmt = select(Decision)
    if assessment_id is not None:
        stmt = stmt.where(Decision.assessment_id == assessment_id)
    if position_id is not None:
        stmt = stmt.where(Decision.position_id == position_id)
    return list((await db.scalars(stmt.order_by(Decision.created_at.desc()))).all())
