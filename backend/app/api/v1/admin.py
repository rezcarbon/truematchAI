"""Admin endpoints: governance config, compliance report, audit query, analytics.

IP-SAFETY: governance endpoints expose gate NAMES and operational status only.
Threshold values are never read from or written to via the API.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.governance import (
    GovernanceConfigError,
    get_governance_config,
    reload_governance_config,
)
from app.deps import CurrentAdmin, DBSession
from app.models.assessment import Assessment, AssessmentStatus
from app.models.audit import AuditTrail
from app.models.decision import Decision
from app.schemas.governance import (
    AnalyticsResponse,
    AuditQueryResponse,
    ComplianceReportResponse,
    GovernanceConfigPatch,
    GovernanceConfigStatus,
)

router = APIRouter()


@router.get("/governance/config", response_model=GovernanceConfigStatus)
async def get_governance_status(admin: CurrentAdmin) -> GovernanceConfigStatus:
    try:
        cfg = get_governance_config()
        return GovernanceConfigStatus(
            configured_gates=cfg.configured_gates(),
            is_placeholder=cfg.is_placeholder(),
            source="external (path-referenced)",
        )
    except GovernanceConfigError:
        # Report status without leaking any detail about values.
        return GovernanceConfigStatus(
            configured_gates=[],
            is_placeholder=True,
            source="unavailable",
        )


@router.patch("/governance/config", response_model=GovernanceConfigStatus)
async def patch_governance_config(
    payload: GovernanceConfigPatch, admin: CurrentAdmin
) -> GovernanceConfigStatus:
    """Patch governance operational settings.

    Accepts only named-key/operational overrides (e.g. enabling gates). Threshold
    VALUES cannot be set here — they are provisioned through the encrypted
    server-side configuration. This triggers a reload of that configuration.
    """
    _ = payload  # named-key overrides would be persisted to company config here
    cfg = reload_governance_config()
    return GovernanceConfigStatus(
        configured_gates=cfg.configured_gates(),
        is_placeholder=cfg.is_placeholder(),
        source="external (path-referenced)",
    )


@router.get("/compliance/report", response_model=ComplianceReportResponse)
async def compliance_report(admin: CurrentAdmin, db: DBSession) -> ComplianceReportResponse:
    total = await db.scalar(select(func.count()).select_from(Assessment)) or 0
    governed = await db.scalar(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.governance_audit_id.isnot(None))
    ) or 0
    counter = await db.scalar(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.counter_rec_triggered.is_(True))
    ) or 0
    overrides = await db.scalar(
        select(func.count())
        .select_from(Decision)
        .where(Decision.ai_recommendation_followed.is_(False))
    ) or 0
    bias_flags = await db.scalar(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.governance_bias_flags.isnot(None))
    ) or 0

    return ComplianceReportResponse(
        generated_at=datetime.now(timezone.utc),
        total_assessments=total,
        governed_assessments=governed,
        counter_recommendations=counter,
        override_count=overrides,
        bias_flags_raised=bias_flags,
        notes="Governance gates evaluated server-side; thresholds not exposed.",
    )


@router.get("/audit", response_model=AuditQueryResponse)
async def query_audit(
    admin: CurrentAdmin,
    db: DBSession,
    assessment_id: uuid.UUID | None = None,
    event_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> AuditQueryResponse:
    stmt = select(AuditTrail)
    count_stmt = select(func.count()).select_from(AuditTrail)
    if assessment_id is not None:
        stmt = stmt.where(AuditTrail.assessment_id == assessment_id)
        count_stmt = count_stmt.where(AuditTrail.assessment_id == assessment_id)
    if event_type is not None:
        stmt = stmt.where(AuditTrail.event_type == event_type)
        count_stmt = count_stmt.where(AuditTrail.event_type == event_type)

    total = await db.scalar(count_stmt) or 0
    rows = list(
        (await db.scalars(stmt.order_by(AuditTrail.created_at.desc()).limit(limit))).all()
    )
    items = [
        {
            "id": str(r.id),
            "assessment_id": str(r.assessment_id) if r.assessment_id else None,
            "event_type": r.event_type,
            "event_data": r.event_data,
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "actor_type": r.actor_type,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return AuditQueryResponse(items=items, total=total)


@router.get("/analytics", response_model=AnalyticsResponse)
async def analytics(admin: CurrentAdmin, db: DBSession) -> AnalyticsResponse:
    total = await db.scalar(select(func.count()).select_from(Assessment)) or 0

    by_status: dict[str, int] = {}
    for st in AssessmentStatus:
        c = await db.scalar(
            select(func.count()).select_from(Assessment).where(Assessment.status == st)
        ) or 0
        by_status[st.value] = c

    avg_delta = await db.scalar(select(func.avg(Assessment.score_delta)))
    counter = await db.scalar(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.counter_rec_triggered.is_(True))
    ) or 0
    decisions_total = await db.scalar(select(func.count()).select_from(Decision)) or 0
    overrides = await db.scalar(
        select(func.count())
        .select_from(Decision)
        .where(Decision.ai_recommendation_followed.is_(False))
    ) or 0

    return AnalyticsResponse(
        generated_at=datetime.now(timezone.utc),
        assessments_total=total,
        assessments_by_status=by_status,
        avg_score_delta=float(avg_delta) if avg_delta is not None else None,
        counter_rec_rate=(counter / total) if total else None,
        decision_override_rate=(overrides / decisions_total) if decisions_total else None,
    )
