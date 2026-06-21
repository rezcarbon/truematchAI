"""Fulfillment + webhook dispatch.

A purchase grants nothing until its Stripe webhook arrives — webhooks are the
source of truth, never the browser redirect. Handling is idempotent: each
Stripe event id is recorded once, so retries/duplicates are safe.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Entitlement, Order, WebhookEvent
from app.services.billing import entitlements as ent
from app.services.billing.catalog import get_sku, limited_skus

logger = logging.getLogger("truematch.billing")


async def sold_count(db: AsyncSession, sku_id: str) -> int:
    """How many of a SKU have been sold (paid OR refunded — a refund frees no
    Founding spot; spots are permanently allocated on purchase)."""
    return int(await db.scalar(
        select(func.count()).select_from(Order).where(
            Order.sku == sku_id, Order.status.in_(("paid", "refunded"))
        )
    ) or 0)


async def founding_inventory(db: AsyncSession) -> list[dict]:
    """Per-tier remaining-spots, for the live Founding 100 counter."""
    out = []
    for s in limited_skus():
        sold = await sold_count(db, s.id)
        out.append({
            "sku": s.id, "name": s.name, "amount": s.amount, "currency": s.currency,
            "limit": s.inventory_limit, "sold": sold,
            "remaining": max(0, s.inventory_limit - sold),
        })
    return out


async def is_sold_out(db: AsyncSession, sku_id: str) -> bool:
    sku = get_sku(sku_id)
    if sku is None or sku.inventory_limit is None:
        return False
    return (await sold_count(db, sku_id)) >= sku.inventory_limit


async def fulfill_order(db: AsyncSession, order: Order) -> None:
    """Grant whatever the order's SKU promises. Safe to skip non-grant SKUs."""
    sku = get_sku(order.sku)
    if sku is None:
        logger.warning("Order %s has unknown sku %s", order.id, order.sku)
        return
    if sku.credits:
        await ent.grant_credits(db, order.user_id, sku.credits, reason=f"purchase:{sku.id}",
                                order_id=order.id)
    if sku.entitlement_kind:
        await ent.grant_entitlement(
            db, order.user_id, kind=sku.entitlement_kind, plan=sku.entitlement_plan,
            days=sku.entitlement_days, monthly_credits=sku.monthly_credits, order_id=order.id,
        )
        # A bounded-credit entitlement (e.g. founding professional = 500/mo)
        # seeds the first cycle's credits immediately.
        if sku.monthly_credits:
            await ent.grant_credits(db, order.user_id, sku.monthly_credits,
                                    reason=f"entitlement:{sku.id}", order_id=order.id)
    # Report SKUs (cv/jd/team) carry no access grant — they're fulfilled by the
    # async/manual pipeline; the paid order is the work ticket.
    order.fulfillment_status = "queued" if sku.report_type else "delivered"
    await db.flush()


async def _order_by_session(db: AsyncSession, session_id: str, client_ref: str | None) -> Order | None:
    if client_ref:
        try:
            o = await db.get(Order, uuid.UUID(client_ref))
            if o:
                return o
        except (ValueError, TypeError):
            pass
    return (
        await db.scalars(select(Order).where(Order.stripe_session_id == session_id))
    ).first()


async def handle_event(db: AsyncSession, event: dict) -> dict:
    """Idempotently process a verified Stripe event. Returns a small summary."""
    event_id = event.get("id")
    event_type = event.get("type", "")
    if event_id:
        existing = (
            await db.scalars(
                select(WebhookEvent).where(WebhookEvent.stripe_event_id == event_id)
            )
        ).first()
        if existing:
            return {"status": "duplicate", "type": event_type}
        db.add(WebhookEvent(stripe_event_id=event_id, event_type=event_type))
        await db.flush()

    obj = (event.get("data") or {}).get("object") or {}
    result = {"status": "ignored", "type": event_type}

    if event_type == "checkout.session.completed":
        order = await _order_by_session(db, obj.get("id"), obj.get("client_reference_id"))
        if order and order.status != "paid":
            order.status = "paid"
            order.stripe_payment_intent = obj.get("payment_intent") or order.stripe_payment_intent
            sub_id = obj.get("subscription")
            await fulfill_order(db, order)
            if sub_id:
                e = await ent.active_entitlement(db, order.user_id)
                if e and e.kind == "subscription":
                    e.stripe_subscription_id = sub_id
            result = {"status": "fulfilled", "order_id": str(order.id), "sku": order.sku}

    elif event_type == "invoice.paid":
        # Subscription renewal — keep the entitlement active (and reseed any
        # bounded monthly credits). Unlimited plans need no top-up.
        sub_id = obj.get("subscription")
        if sub_id:
            e = (await db.scalars(
                select(Entitlement).where(Entitlement.stripe_subscription_id == sub_id)
            )).first()
            if e:
                e.status = "active"
                if e.monthly_credits:
                    await ent.grant_credits(db, e.user_id, e.monthly_credits,
                                            reason="subscription_renewal")
                result = {"status": "renewed", "entitlement_id": str(e.id)}

    elif event_type in ("customer.subscription.deleted", "customer.subscription.canceled"):
        sub_id = obj.get("id")
        e = (await db.scalars(
            select(Entitlement).where(Entitlement.stripe_subscription_id == sub_id)
        )).first()
        if e:
            e.status = "canceled"
            result = {"status": "canceled", "entitlement_id": str(e.id)}

    await db.commit()
    return result
