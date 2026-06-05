"""Position endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DBSession
from app.engines import corpus, jd_evolution, reasoning
from app.engines.intake import analyze_jd
from app.models.jd_version import JDVersion
from app.models.position import Position
from app.models.user import UserRole
from app.schemas.position import (
    PositionCreate,
    PositionList,
    PositionResponse,
    PositionUpdate,
)

router = APIRouter()


def _require_recruiter(user: CurrentUser) -> None:
    if user.role not in (UserRole.recruiter, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter role required"
        )


async def _snapshot_jd(db: DBSession, position: Position) -> None:
    """Append an immutable JD version snapshot (Pillar 3 history + audit record)."""
    count = await db.scalar(
        select(func.count()).select_from(JDVersion).where(JDVersion.position_id == position.id)
    )
    db.add(
        JDVersion(
            position_id=position.id,
            version=(count or 0) + 1,
            description=position.description,
            parsed_requirements=position.parsed_requirements,
            jd_quality_score=position.jd_quality_score,
            jd_issues=position.jd_issues,
        )
    )
    await db.flush()


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    payload: PositionCreate, user: CurrentUser, db: DBSession
) -> Position:
    _require_recruiter(user)
    company_id = payload.company_id or user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="company_id required (user has no company)",
        )

    # Synchronous JD analysis + interrogation for immediate quality feedback.
    requirements = analyze_jd(payload.description or "")
    jd_review = reasoning.interrogate_jd(payload.description or "")

    position = Position(
        company_id=company_id,
        created_by=user.id,
        title=payload.title,
        description=payload.description,
        parsed_requirements=requirements,
        jd_quality_score=jd_review.get("quality_score"),
        jd_issues={"issues": jd_review.get("issues", [])},
    )
    db.add(position)
    await db.flush()
    await _snapshot_jd(db, position)  # version 1
    await corpus.record_jd(db, position.description or "")  # corpus learning
    return position


@router.get("", response_model=PositionList)
async def list_positions(user: CurrentUser, db: DBSession) -> PositionList:
    stmt = select(Position)
    count_stmt = select(func.count()).select_from(Position)
    if user.company_id is not None:
        stmt = stmt.where(Position.company_id == user.company_id)
        count_stmt = count_stmt.where(Position.company_id == user.company_id)
    total = await db.scalar(count_stmt) or 0
    items = list((await db.scalars(stmt.order_by(Position.created_at.desc()))).all())
    return PositionList(
        items=[PositionResponse.model_validate(p) for p in items], total=total
    )


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> Position:
    position = await db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    return position


@router.patch("/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: uuid.UUID, payload: PositionUpdate, user: CurrentUser, db: DBSession
) -> Position:
    _require_recruiter(user)
    position = await db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(position, key, value)
    # A description change re-runs JD analysis and snapshots a new version so the
    # evolution engine has a longitudinal record.
    if "description" in data:
        requirements = analyze_jd(position.description or "")
        jd_review = reasoning.interrogate_jd(position.description or "")
        position.parsed_requirements = requirements
        position.jd_quality_score = jd_review.get("quality_score")
        position.jd_issues = {"issues": jd_review.get("issues", [])}
        await db.flush()
        await _snapshot_jd(db, position)
        await corpus.record_jd(db, position.description or "")  # corpus learning
    else:
        await db.flush()
    return position


@router.get("/{position_id}/jd-versions")
async def list_jd_versions(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    """Immutable JD version history for a position (Pillar 3 + audit record)."""
    versions = list(
        (
            await db.scalars(
                select(JDVersion)
                .where(JDVersion.position_id == position_id)
                .order_by(JDVersion.version)
            )
        ).all()
    )
    return {
        "position_id": str(position_id),
        "versions": [
            {
                "version": v.version,
                "jd_quality_score": v.jd_quality_score,
                "parsed_requirements": v.parsed_requirements,
                "jd_issues": v.jd_issues,
                "created_at": v.created_at,
            }
            for v in versions
        ],
    }


@router.get("/{position_id}/evolution")
async def get_jd_evolution(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> dict:
    """How the role's JD has evolved + how it should evolve next (Pillar 3)."""
    versions = list(
        (
            await db.scalars(
                select(JDVersion)
                .where(JDVersion.position_id == position_id)
                .order_by(JDVersion.version)
            )
        ).all()
    )
    history = [
        {
            "version": v.version,
            "description": v.description,
            "parsed_requirements": v.parsed_requirements,
            "jd_quality_score": v.jd_quality_score,
            "jd_issues": v.jd_issues,
        }
        for v in versions
    ]
    return jd_evolution.analyze_evolution(history)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    position_id: uuid.UUID, user: CurrentUser, db: DBSession
) -> None:
    _require_recruiter(user)
    position = await db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    await db.delete(position)
    return None
