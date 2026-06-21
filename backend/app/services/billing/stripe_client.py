"""Thin, gated wrapper around the Stripe SDK.

Gated exactly like every other external integration: with no secret key,
``is_configured()`` is False and callers raise ``BillingError`` (mapped to a
clean 503) rather than pretending. Only Stripe-hosted Checkout is used — card
data never touches our servers (PCI SAQ A).
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger("truematch.billing")


class BillingError(RuntimeError):
    """Raised when billing is unconfigured or a Stripe call fails."""


def is_configured() -> bool:
    return settings.stripe_configured


def _stripe():
    if not settings.stripe_configured:
        raise BillingError("Billing is not configured (no Stripe key).")
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


def create_checkout_session(
    *,
    sku_id: str,
    mode: str,
    amount: int,
    currency: str,
    product_name: str,
    quantity: int,
    customer_email: str | None,
    client_reference_id: str,
    metadata: dict,
    allow_promotion_codes: bool = True,
) -> dict:
    """Create a Stripe Checkout session with inline price_data. Returns
    ``{"id", "url"}``. Raises BillingError if unconfigured / on failure."""
    stripe = _stripe()
    line_item = {
        "price_data": {
            "currency": currency,
            "product_data": {"name": product_name},
            "unit_amount": amount,
            **({"recurring": {"interval": "month"}} if mode == "subscription" else {}),
        },
        "quantity": quantity,
    }
    try:
        session = stripe.checkout.Session.create(
            mode=mode,  # "payment" | "subscription"
            line_items=[line_item],
            success_url=settings.billing_success_url,
            cancel_url=settings.billing_cancel_url,
            client_reference_id=client_reference_id,
            customer_email=customer_email or None,
            metadata={"sku": sku_id, **metadata},
            allow_promotion_codes=allow_promotion_codes,
        )
    except Exception as exc:  # noqa: BLE001 — surface as billing error
        logger.warning("Stripe checkout create failed: %s", exc)
        raise BillingError(f"Could not create checkout session: {exc}") from exc
    return {"id": session.id, "url": session.url}


def construct_event(payload: bytes, sig_header: str) -> dict:
    """Verify a webhook payload's signature and return the event dict.

    Requires ``stripe_webhook_secret``; raises BillingError on bad signature.
    """
    if not settings.stripe_webhook_secret:
        raise BillingError("Webhook secret not configured.")
    stripe = _stripe()
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except Exception as exc:  # noqa: BLE001 — invalid signature / payload
        raise BillingError(f"Invalid webhook signature: {exc}") from exc
    return event


def refund(payment_intent: str) -> dict:
    """Refund a payment intent in full. Returns the Stripe refund object."""
    stripe = _stripe()
    try:
        r = stripe.Refund.create(payment_intent=payment_intent)
    except Exception as exc:  # noqa: BLE001
        raise BillingError(f"Refund failed: {exc}") from exc
    return {"id": r.id, "status": r.status}
