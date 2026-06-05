"""Governance / admin schemas.

IP-SAFETY: these schemas intentionally expose only gate NAMES and qualitative
status. Threshold values are never represented here.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GovernanceConfigStatus(BaseModel):
    """Admin view of governance config — names + operational status only."""

    configured_gates: list[str]
    is_placeholder: bool
    source: str = Field(description="Where the config is loaded from (path label only).")


class GovernanceConfigPatch(BaseModel):
    """Patch request for per-company governance overrides.

    Accepts named-key overrides only. Numeric threshold values are rejected
    and must be managed through the encrypted server-side configuration.
    """

    enabled_gates: list[str] | None = None
    company_id: uuid.UUID | None = None


class ComplianceReportResponse(BaseModel):
    generated_at: datetime
    total_assessments: int
    governed_assessments: int
    counter_recommendations: int
    override_count: int
    bias_flags_raised: int
    notes: str | None = None


class AuditQueryResponse(BaseModel):
    items: list[dict]
    total: int


class AnalyticsResponse(BaseModel):
    generated_at: datetime
    assessments_total: int
    assessments_by_status: dict[str, int]
    avg_score_delta: float | None
    counter_rec_rate: float | None
    decision_override_rate: float | None
