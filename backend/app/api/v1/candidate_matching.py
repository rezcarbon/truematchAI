"""Candidate matching and notification APIs.

Handles:
- Match notifications timeline
- Candidate match details
- Privacy preferences
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user
from app.models import MatchNotification, CandidateMatch, User

router = APIRouter(prefix="/candidate/matches", tags=["candidate-matching"])


@router.get("/notifications/{match_id}")
async def get_match_notifications(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get timeline of notifications for a specific candidate match.

    Returns events showing profile sent, viewed, interview scheduled, etc.
    Candidate can only see their own matches.
    """
    match = await db.get(CandidateMatch, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.candidate_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this match")

    # Get notifications sorted by timestamp
    notifications = await db.execute(
        "SELECT * FROM match_notifications WHERE candidate_match_id = ? ORDER BY status_timestamp DESC",
        (match_id,),
    )

    return {
        "match_id": match_id,
        "events": [
            {
                "id": str(n.id),
                "status": n.status.value,
                "message": n.message,
                "timestamp": n.status_timestamp.isoformat(),
                "emailSent": n.email_sent,
            }
            for n in notifications.scalars().all()
        ],
    }


@router.get("/{match_id}")
async def get_candidate_match(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get match details including persona info and notifications.

    Candidate can only see their own matches.
    """
    match = await db.get(CandidateMatch, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.candidate_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this match")

    return {
        "id": str(match.id),
        "position_id": str(match.position_id),
        "overall_score": match.overall_score,
        "fit_level": match.fit_level.value,
        "matched_by_persona": match.matched_by_persona,
        "persona_confidence": match.persona_confidence,
        "persona_reasoning": match.persona_reasoning,
        "concerns": match.concerns,
        "opportunities": match.opportunities,
    }
