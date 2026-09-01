"""Product catalog — the single source of truth for what TrueMatch sells.

Prices are defined in code (cents) rather than in a DB table for v1: it keeps
the catalog reviewable, versioned, and impossible to tamper with via the API.
Each SKU declares what a successful purchase GRANTS:

  - ``credits``            → N assessment credits added to the buyer's ledger
  - ``entitlement``        → time-boxed access ("founding"/"subscription") with
                             a plan + duration (days) and optional monthly credit
  - ``report``             → a one-off deliverable (CV/JD/team report) — fulfilled
                             by the manual/async pipeline, no recurring access

A SKU is either ``mode="payment"`` (one-time) or ``mode="subscription"``
(recurring, via Stripe Billing). Amounts are in the smallest currency unit.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sku:
    id: str
    name: str
    description: str
    amount: int            # smallest currency unit (e.g. cents)
    currency: str = "usd"
    mode: str = "payment"  # "payment" | "subscription"
    # What a successful purchase grants:
    credits: int = 0                 # assessment credits added to the ledger
    entitlement_kind: str | None = None   # "founding" | "subscription" | None
    entitlement_plan: str | None = None   # "candidate" | "premium" | "starter" …
    entitlement_days: int = 0             # access duration for one-time founding
    monthly_credits: int | None = None    # per-cycle credit grant (None = unlimited)
    report_type: str | None = None        # "cv" | "jd" | "jd_comprehensive" | "team"
    public: bool = True                   # listed on the public catalog endpoint
    inventory_limit: int | None = None    # finite stock (Founding 100), else unlimited


# Singapore-friendly USD pricing per the launch strategy. Single assessment is
# priced at $3 (not $1) so Stripe's per-txn fee isn't ~33%; the 5-pack is the
# hero SKU. Founding tiers are ONE-TIME purchases that grant 12-month access
# (not auto-renewing subscriptions).
CATALOG: dict[str, Sku] = {
    s.id: s
    for s in [
        Sku("assessment_single", "Single assessment", "One capability assessment (CV vs JD).",
            300, credits=1),
        Sku("assessment_5pack", "5 assessments", "Five capability assessments — best value.",
            900, credits=5),
        Sku("cv_analysis", "CV analysis", "Capability profile of a CV (no target JD).",
            500, credits=0, report_type="cv"),
        Sku("jd_report_basic", "JD quality report", "JD interrogation: quality, proxies, fixes.",
            5000, report_type="jd", public=True),
        Sku("jd_report_comprehensive", "JD report (comprehensive)",
            "JD report + archetype analysis + rewrite recommendations.",
            20000, report_type="jd_comprehensive"),
        Sku("team_assessment", "Team assessment", "Capability map for 10–50 team members.",
            50000, report_type="team"),
        # Founding 100 — one-time, 12-month access.
        Sku("founding_candidate", "Founding Candidate",
            "12 months unlimited assessments + founding badge + early access.",
            4900, entitlement_kind="founding", entitlement_plan="candidate",
            entitlement_days=365, monthly_credits=None, inventory_limit=60),
        Sku("founding_enterprise", "Founding Enterprise",
            "12 months Professional tier (500 assessments/mo) + priority onboarding.",
            49900, entitlement_kind="founding", entitlement_plan="professional",
            entitlement_days=365, monthly_credits=500, inventory_limit=30),
        Sku("founding_partner", "Founding Partner",
            "12 months unlimited enterprise + priority ATS setup + strategy calls.",
            250000, entitlement_kind="founding", entitlement_plan="enterprise",
            entitlement_days=365, monthly_credits=None, inventory_limit=10),
        # Recurring subscription (post-cloud GA).
        Sku("premium_monthly", "Premium (monthly)",
            "Unlimited assessments, real-time results.",
            990, mode="subscription", entitlement_kind="subscription",
            entitlement_plan="premium", monthly_credits=None),
    ]
}

# Plans that grant UNLIMITED assessments (no credit decrement while active).
UNLIMITED_PLANS = frozenset({"candidate", "enterprise", "premium"})


def get_sku(sku_id: str) -> Sku | None:
    return CATALOG.get(sku_id)


def limited_skus() -> list[Sku]:
    """SKUs with a finite inventory cap (the Founding 100 tiers)."""
    return [s for s in CATALOG.values() if s.inventory_limit is not None]


def public_catalog() -> list[dict]:
    out = []
    for s in CATALOG.values():
        if not s.public:
            continue
        out.append({
            "id": s.id, "name": s.name, "description": s.description,
            "amount": s.amount, "currency": s.currency, "mode": s.mode,
            "credits": s.credits, "entitlement_kind": s.entitlement_kind,
            "entitlement_plan": s.entitlement_plan,
        })
    return out
