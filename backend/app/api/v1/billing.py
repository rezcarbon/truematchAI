"""Billing & payments endpoints.

Stripe-hosted Checkout only (no card data on our servers). Webhooks are the
source of truth for fulfillment; the browser redirect grants nothing. The
catalog is public; checkout/status require auth; refunds require admin.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.config import settings
from app.deps import CurrentAdmin, CurrentUser, DBSession
from app.models.billing import Coupon, Order
from app.models.user import User
from app.services.billing import entitlements as ent
from app.services.billing import service as billing_service
from app.services.billing.catalog import get_sku, public_catalog
from app.services.billing.stripe_client import BillingError, construct_event, create_checkout_session, refund

logger = logging.getLogger("truematch.billing")
router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/catalog")
async def catalog() -> dict:
    """Public product catalog for the pricing page."""
    return {"items": public_catalog(), "configured": settings.stripe_configured}


@router.get("/founding")
async def founding(db: DBSession) -> dict:
    """Live Founding-100 inventory: remaining spots per tier (public)."""
    return {"tiers": await billing_service.founding_inventory(db)}


class CheckoutRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(1, ge=1, le=50)


@router.post("/checkout")
async def checkout(payload: CheckoutRequest, user: CurrentUser, db: DBSession) -> dict:
    """Create a Stripe Checkout session for a SKU; returns the redirect URL."""
    if not settings.stripe_configured:
        raise HTTPException(status_code=503, detail="Billing is not configured.")
    sku = get_sku(payload.sku)
    if sku is None:
        raise HTTPException(status_code=404, detail=f"Unknown product '{payload.sku}'")
    # Finite-inventory SKUs (Founding 100): refuse once sold out.
    if sku.inventory_limit is not None and await billing_service.is_sold_out(db, sku.id):
        raise HTTPException(status_code=409, detail=f"{sku.name} is sold out.")

    order = Order(
        user_id=user.id, sku=sku.id,
        amount=sku.amount * payload.quantity, currency=sku.currency, status="pending",
    )
    db.add(order)
    await db.flush()

    try:
        sess = create_checkout_session(
            sku_id=sku.id, mode=sku.mode, amount=sku.amount, currency=sku.currency,
            product_name=sku.name, quantity=payload.quantity,
            customer_email=getattr(user, "email", None),
            client_reference_id=str(order.id),
            metadata={"user_id": str(user.id)},
        )
    except BillingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    order.stripe_session_id = sess["id"]
    await db.commit()
    return {"order_id": str(order.id), "checkout_url": sess["url"]}


@router.post("/webhook")
async def webhook(request: Request, db: DBSession) -> dict:
    """Stripe webhook — signature-verified and idempotent. The ONLY place that
    grants credits/entitlements."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = construct_event(payload, sig)
    except BillingError as exc:
        # 400 so Stripe retries on transient issues but not on bad signatures.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = await billing_service.handle_event(db, event)
    return {"received": True, **result}


@router.get("/me")
async def my_billing(user: CurrentUser, db: DBSession) -> dict:
    """The caller's access summary (entitlement + credit balance) + recent orders."""
    summary = await ent.access_summary(db, user.id)
    orders = (
        await db.scalars(
            select(Order).where(Order.user_id == user.id)
            .order_by(Order.created_at.desc()).limit(20)
        )
    ).all()
    summary["orders"] = [
        {
            "id": str(o.id), "sku": o.sku, "amount": o.amount, "currency": o.currency,
            "status": o.status, "fulfillment_status": o.fulfillment_status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]
    return summary


class RedeemRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)


@router.post("/redeem")
async def redeem(payload: RedeemRequest, user: CurrentUser, db: DBSession) -> dict:
    """Redeem a free-credit coupon (NTUC / referral). Discount coupons are
    handled by Stripe promotion codes at checkout, not here."""
    coupon = (
        await db.scalars(select(Coupon).where(Coupon.code == payload.code))
    ).first()
    if coupon is None or not coupon.active:
        raise HTTPException(status_code=404, detail="Invalid or inactive code.")
    if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Code has expired.")
    if coupon.max_redemptions is not None and coupon.redeemed_count >= coupon.max_redemptions:
        raise HTTPException(status_code=409, detail="Code fully redeemed.")
    if coupon.grant_credits <= 0:
        raise HTTPException(status_code=400, detail="This code is not redeemable for credits.")

    await ent.grant_credits(db, user.id, coupon.grant_credits, reason=f"coupon:{coupon.code}")
    coupon.redeemed_count += 1
    await db.commit()
    return {"granted_credits": coupon.grant_credits, "balance": await ent.credit_balance(db, user.id)}


# ── Referrals ────────────────────────────────────────────────────────────────

@router.get("/referral")
async def my_referral(user: CurrentUser, db: DBSession) -> dict:
    """The caller's referral code + share base + stats (creates code on first call)."""
    from app.services.billing import referral
    return await referral.stats(db, user.id)


class RedeemReferralRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=32)


@router.post("/referral/redeem")
async def redeem_referral(payload: RedeemReferralRequest, user: CurrentUser, db: DBSession) -> dict:
    """Redeem a referral code — credits both the new user and the referrer."""
    from app.services.billing import referral
    if not settings.referral_enabled:
        raise HTTPException(status_code=404, detail="Referrals are not enabled.")
    try:
        return await referral.redeem(db, user.id, payload.code)
    except referral.ReferralError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/share/{token}")
async def public_shared_result(token: str, db: DBSession) -> dict:
    """PUBLIC anonymised result snapshot (scores + delta only — no PII).

    Unauthenticated by design: it's the shareable page. Returns 404 for an
    unknown token (opaque, non-enumerable)."""
    from app.services.billing import referral
    data = await referral.get_share(db, token)
    if data is None:
        raise HTTPException(status_code=404, detail="Shared result not found")
    return data


class RefundRequest(BaseModel):
    order_id: uuid.UUID


@router.post("/refund")
async def refund_order(payload: RefundRequest, admin: CurrentAdmin, db: DBSession) -> dict:
    """Refund a paid order (admin / Delta-Challenge). Reverses purchased credits."""
    order = await db.get(Order, payload.order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "paid":
        raise HTTPException(status_code=409, detail=f"Order is {order.status}, not paid")
    if not order.stripe_payment_intent:
        raise HTTPException(status_code=409, detail="Order has no payment to refund")
    try:
        refund(order.stripe_payment_intent)
    except BillingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    order.status = "refunded"
    # Claw back purchased credits (best-effort; balance may go negative if spent).
    sku = get_sku(order.sku)
    if sku and sku.credits:
        from app.models.billing import CreditLedger
        db.add(CreditLedger(user_id=order.user_id, delta=-sku.credits,
                            reason=f"refund:{order.sku}", order_id=order.id))
    await db.commit()
    return {"order_id": str(order.id), "status": "refunded"}


# ── Admin: orders / fulfillment queue (the 48h manual bridge) ────────────────

_FULFILLMENT_STATES = ("pending", "queued", "processing", "delivered")


@router.get("/admin/orders")
async def admin_orders(
    admin: CurrentAdmin,
    db: DBSession,
    status_filter: str | None = None,
    fulfillment: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """All orders for the fulfillment console (filterable, newest first)."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    stmt = select(Order, User.email).join(User, User.id == Order.user_id)
    count_stmt = select(func.count()).select_from(Order)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
        count_stmt = count_stmt.where(Order.status == status_filter)
    if fulfillment:
        stmt = stmt.where(Order.fulfillment_status == fulfillment)
        count_stmt = count_stmt.where(Order.fulfillment_status == fulfillment)
    total = await db.scalar(count_stmt) or 0
    rows = (
        await db.execute(
            stmt.order_by(Order.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    items = [
        {
            "id": str(o.id), "user_email": email, "sku": o.sku,
            "amount": o.amount, "currency": o.currency, "status": o.status,
            "fulfillment_status": o.fulfillment_status,
            "stripe_payment_intent": o.stripe_payment_intent,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for (o, email) in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


class FulfillmentUpdate(BaseModel):
    fulfillment_status: str = Field(..., description="pending|queued|processing|delivered")
    note: str | None = Field(None, max_length=2000)


@router.patch("/admin/orders/{order_id}/fulfillment")
async def admin_set_fulfillment(
    order_id: uuid.UUID, payload: FulfillmentUpdate, admin: CurrentAdmin, db: DBSession
) -> dict:
    """Advance an order through the manual fulfillment pipeline."""
    if payload.fulfillment_status not in _FULFILLMENT_STATES:
        raise HTTPException(status_code=422, detail=f"Invalid status. One of {_FULFILLMENT_STATES}")
    order = await db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.fulfillment_status = payload.fulfillment_status
    if payload.note:
        extra = dict(order.extra or {})
        log = list(extra.get("fulfillment_log", []))
        log.append({
            "status": payload.fulfillment_status, "note": payload.note,
            "by": str(admin.id), "at": datetime.now(timezone.utc).isoformat(),
        })
        extra["fulfillment_log"] = log
        order.extra = extra
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(order, "extra")
    await db.commit()
    return {"id": str(order.id), "fulfillment_status": order.fulfillment_status}


@router.get("/admin/summary")
async def admin_summary(admin: CurrentAdmin, db: DBSession) -> dict:
    """Revenue + fulfillment-queue snapshot + Founding inventory for the dashboard."""
    paid = (
        await db.execute(
            select(func.count(), func.coalesce(func.sum(Order.amount), 0))
            .where(Order.status == "paid")
        )
    ).one()
    awaiting = await db.scalar(
        select(func.count()).select_from(Order).where(
            Order.status == "paid",
            Order.fulfillment_status.in_(("pending", "queued", "processing")),
        )
    ) or 0
    refunded = await db.scalar(
        select(func.count()).select_from(Order).where(Order.status == "refunded")
    ) or 0
    return {
        "paid_orders": int(paid[0]),
        "gross_revenue": int(paid[1]),   # smallest currency unit
        "awaiting_fulfillment": int(awaiting),
        "refunded_orders": int(refunded),
        "founding": await billing_service.founding_inventory(db),
    }
