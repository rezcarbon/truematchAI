"""Entitlement & credit logic — the access layer the rest of the app checks.

Access to a metered action (an assessment) is granted when the user EITHER has
an active unlimited entitlement OR a positive credit balance. Credits live in
an append-only ledger (balance = SUM(delta)); entitlements are time-boxed
(founding) or recurring (subscription).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import CreditLedger, Entitlement
from app.services.billing.catalog import UNLIMITED_PLANS

logger = logging.getLogger("truematch.billing")


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def credit_balance(db: AsyncSession, user_id: uuid.UUID) -> int:
    total = await db.scalar(
        select(func.coalesce(func.sum(CreditLedger.delta), 0)).where(
            CreditLedger.user_id == user_id
        )
    )
    return int(total or 0)


async def grant_credits(
    db: AsyncSession, user_id: uuid.UUID, n: int, reason: str,
    order_id: uuid.UUID | None = None,
) -> None:
    if n <= 0:
        return
    db.add(CreditLedger(user_id=user_id, delta=n, reason=reason, order_id=order_id))
    await db.flush()


async def active_entitlement(db: AsyncSession, user_id: uuid.UUID) -> Entitlement | None:
    """The user's current active, non-expired entitlement (if any)."""
    rows = (
        await db.scalars(
            select(Entitlement)
            .where(Entitlement.user_id == user_id, Entitlement.status == "active")
            .order_by(Entitlement.created_at.desc())
        )
    ).all()
    now = _now()
    for e in rows:
        if e.expires_at is None or e.expires_at > now:
            return e
    return None


async def has_unlimited_access(db: AsyncSession, user_id: uuid.UUID) -> bool:
    e = await active_entitlement(db, user_id)
    return bool(e and e.monthly_credits is None and e.plan in UNLIMITED_PLANS)


async def has_access(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """True when the user may run a metered action right now."""
    if await has_unlimited_access(db, user_id):
        return True
    return (await credit_balance(db, user_id)) > 0


async def consume_credit(
    db: AsyncSession, user_id: uuid.UUID, assessment_id: uuid.UUID | None = None
) -> bool:
    """Spend one unit of access. Returns True if access was available.

    Unlimited entitlements are not decremented; otherwise one credit is spent
    (recorded as a -1 ledger row). Returns False when there is no access.
    """
    if await has_unlimited_access(db, user_id):
        return True
    if (await credit_balance(db, user_id)) <= 0:
        return False
    db.add(CreditLedger(
        user_id=user_id, delta=-1, reason="assessment", assessment_id=assessment_id
    ))
    await db.flush()
    return True


async def grant_entitlement(
    db: AsyncSession, user_id: uuid.UUID, *, kind: str, plan: str,
    days: int = 0, monthly_credits: int | None = None,
    order_id: uuid.UUID | None = None, stripe_subscription_id: str | None = None,
) -> Entitlement:
    now = _now()
    ent = Entitlement(
        user_id=user_id, kind=kind, plan=plan, status="active",
        starts_at=now,
        expires_at=(now + timedelta(days=days)) if days else None,
        monthly_credits=monthly_credits,
        stripe_subscription_id=stripe_subscription_id,
        source_order_id=order_id,
    )
    db.add(ent)
    await db.flush()
    return ent


async def access_summary(db: AsyncSession, user_id: uuid.UUID) -> dict:
    e = await active_entitlement(db, user_id)
    bal = await credit_balance(db, user_id)
    unlimited = bool(e and e.monthly_credits is None and e.plan in UNLIMITED_PLANS)
    return {
        "has_access": unlimited or bal > 0,
        "credit_balance": bal,
        "unlimited": unlimited,
        "entitlement": None if e is None else {
            "kind": e.kind, "plan": e.plan, "status": e.status,
            "expires_at": e.expires_at.isoformat() if e.expires_at else None,
            "monthly_credits": e.monthly_credits,
        },
    }
