"""Capability-profile schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.profile import ProfileVisibility


class UserProfileUpdate(BaseModel):
    """Update user profile fields (display name, location, headline)."""
    display_name: str | None = None
    location: str | None = None
    headline: str | None = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    location: str | None
    headline: str | None
    role: str


class ProfileUpdate(BaseModel):
    visibility: ProfileVisibility | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    narrative: str | None
    trajectory_summary: dict | None
    top_capabilities: dict | None
    assessment_count: int
    share_token: str | None
    visibility: ProfileVisibility


class PublicProfileResponse(BaseModel):
    """Profile view served via share token — omits internal identifiers."""

    narrative: str | None
    trajectory_summary: dict | None
    top_capabilities: dict | None
    assessment_count: int


class ShareTokenResponse(BaseModel):
    share_token: str
    visibility: ProfileVisibility
