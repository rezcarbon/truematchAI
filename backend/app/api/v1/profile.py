"""Capability-profile endpoints."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DBSession
from app.models.assessment import Assessment
from app.models.audit import AuditTrail
from app.models.decision import Decision
from app.models.profile import CapabilityProfile, ProfileVisibility
from app.models.resume import Resume
from app.models.user import User
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdate,
    PublicProfileResponse,
    ShareTokenResponse,
    UserProfileResponse,
    UserProfileUpdate,
)

router = APIRouter()


async def _get_or_create_profile(user_id, db) -> CapabilityProfile:
    profile = await db.scalar(
        select(CapabilityProfile).where(CapabilityProfile.user_id == user_id)
    )
    if profile is None:
        profile = CapabilityProfile(user_id=user_id)
        db.add(profile)
        await db.flush()
    return profile


# --- User profile endpoints (display name, location, headline) ---


@router.get("/user/me", response_model=UserProfileResponse)
async def get_my_user_profile(user: CurrentUser, db: DBSession) -> User:
    """Get the current user's profile (name, location, headline)."""
    return user


@router.patch("/user/me", response_model=UserProfileResponse)
async def update_my_user_profile(
    payload: UserProfileUpdate, user: CurrentUser, db: DBSession
) -> User:
    """Update the current user's profile fields.

    Updates display_name, location, and headline.
    """
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.location is not None:
        user.location = payload.location
    if payload.headline is not None:
        user.headline = payload.headline

    await db.flush()
    return user


# --- Capability profile endpoints (narrative, visibility, sharing) ---


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(user: CurrentUser, db: DBSession) -> CapabilityProfile:
    return await _get_or_create_profile(user.id, db)


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    payload: ProfileUpdate, user: CurrentUser, db: DBSession
) -> CapabilityProfile:
    profile = await _get_or_create_profile(user.id, db)
    if payload.visibility is not None:
        profile.visibility = payload.visibility
    await db.flush()
    return profile


@router.post("/me/share", response_model=ShareTokenResponse)
async def create_share_token(user: CurrentUser, db: DBSession) -> ShareTokenResponse:
    profile = await _get_or_create_profile(user.id, db)
    profile.share_token = secrets.token_urlsafe(24)
    if profile.visibility == ProfileVisibility.private:
        profile.visibility = ProfileVisibility.link
    await db.flush()
    return ShareTokenResponse(share_token=profile.share_token, visibility=profile.visibility)


@router.get("/shared/{share_token}", response_model=PublicProfileResponse)
async def get_shared_profile(share_token: str, db: DBSession) -> PublicProfileResponse:
    """Public, token-gated view. No auth required; omits internal identifiers."""
    profile = await db.scalar(
        select(CapabilityProfile).where(CapabilityProfile.share_token == share_token)
    )
    if profile is None or profile.visibility == ProfileVisibility.private:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return PublicProfileResponse(
        narrative=profile.narrative,
        trajectory_summary=profile.trajectory_summary,
        top_capabilities=profile.top_capabilities,
        assessment_count=profile.assessment_count,
    )


# --- PDPA / GDPR: data portability + right to erasure -----------------------

@router.post("/export")
async def export_my_data(user: CurrentUser, db: DBSession) -> dict:
    """Export all of the requesting user's personal data (PDPA/GDPR portability).

    Values are decrypted transparently on read; this is the user's own data.
    """
    profile = await db.scalar(
        select(CapabilityProfile).where(CapabilityProfile.user_id == user.id)
    )
    resumes = (await db.scalars(select(Resume).where(Resume.user_id == user.id))).all()
    assessments = (
        await db.scalars(select(Assessment).where(Assessment.user_id == user.id))
    ).all()
    decisions = (
        await db.scalars(select(Decision).where(Decision.recruiter_id == user.id))
    ).all()

    return {
        "format": "truematch.data-export.v1",
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role.value,
            "created_at": user.created_at,
        },
        "profile": None
        if profile is None
        else {
            "narrative": profile.narrative,
            "trajectory_summary": profile.trajectory_summary,
            "top_capabilities": profile.top_capabilities,
            "assessment_count": profile.assessment_count,
            "visibility": profile.visibility.value,
        },
        "resumes": [
            {
                "id": r.id,
                "file_type": r.file_type,
                "parsed_data": r.parsed_data,
                "raw_narrative": r.raw_narrative,
                "supplementary": r.supplementary,
                "created_at": r.created_at,
            }
            for r in resumes
        ],
        "assessments": [
            {
                "id": a.id,
                "status": a.status.value,
                "traditional_score": a.traditional_score,
                "capability_score": a.capability_score,
                "score_delta": a.score_delta,
                "capability_narrative": a.capability_narrative,
                "trajectory_narrative": a.trajectory_narrative,
                "counter_rec_reasoning": a.counter_rec_reasoning,
                "created_at": a.created_at,
            }
            for a in assessments
        ],
        "decisions_made": [
            {
                "id": d.id,
                "assessment_id": d.assessment_id,
                "decision": d.decision.value,
                "override_reasoning": d.override_reasoning,
                "cultural_fit_notes": d.cultural_fit_notes,
                "interview_notes": d.interview_notes,
                "created_at": d.created_at,
            }
            for d in decisions
        ],
    }


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def erase_my_data(user: CurrentUser, db: DBSession) -> None:
    """Right to erasure (PDPA/GDPR). Deletes the user and all associated data.

    Resumes, assessments, the capability profile, and related audit rows are
    removed by database FK cascade. A minimal, unlinked compliance tombstone is
    written first so the erasure itself remains provable.
    """
    db.add(
        AuditTrail(
            assessment_id=None,
            event_type="user.erased",
            actor_id=user.id,
            actor_type="user",
            event_data={"erased_user_id": str(user.id)},
        )
    )
    await db.flush()
    await db.delete(user)
    return None
