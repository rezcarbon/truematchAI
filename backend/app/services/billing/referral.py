"""Referral mechanic + shareable anonymised results.

Two-sided: a successful referral grants free credits to BOTH the referrer and
the new referee. Anti-abuse: a user cannot redeem their own code, and a user
can only ever be referred once (enforced by a unique referee constraint + a
pre-check). Shared results expose ONLY scores — never the narrative or PII.
"""
from __future__ import annotations

import logging
import secrets
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.referral import ReferralCode, ReferralRedemption, SharedResult
from app.services.billing import entitlements as ent

logger = logging.getLogger("truematch.referral")


class ReferralError(RuntimeError):
    """Raised on invalid/abusive redemption attempts (mapped to 4xx)."""


async def get_or_create_code(db: AsyncSession, user_id: uuid.UUID) -> ReferralCode:
    rc = (
        await db.scalars(select(ReferralCode).where(ReferralCode.user_id == user_id))
    ).first()
    if rc:
        return rc
    # Short, URL-safe, collision-checked.
    for _ in range(5):
        code = secrets.token_urlsafe(6).replace("_", "").replace("-", "")[:8].upper()
        exists = (await db.scalars(select(ReferralCode).where(ReferralCode.code == code))).first()
        if not exists:
            break
    rc = ReferralCode(user_id=user_id, code=code)
    db.add(rc)
    await db.flush()
    return rc


async def redeem(db: AsyncSession, referee_user_id: uuid.UUID, code: str) -> dict:
    """Redeem a referral code. Grants credits to referee and referrer."""
    rc = (await db.scalars(select(ReferralCode).where(ReferralCode.code == code.strip()))).first()
    if rc is None:
        raise ReferralError("Invalid referral code.")
    if rc.user_id == referee_user_id:
        raise ReferralError("You can't redeem your own referral code.")
    already = (
        await db.scalars(
            select(ReferralRedemption).where(ReferralRedemption.referee_user_id == referee_user_id)
        )
    ).first()
    if already:
        raise ReferralError("You've already used a referral code.")

    reward = settings.referral_reward_credits
    await ent.grant_credits(db, referee_user_id, reward, reason=f"referral_referee:{rc.code}")
    await ent.grant_credits(db, rc.user_id, reward, reason=f"referral_referrer:{rc.code}")
    db.add(ReferralRedemption(
        code_id=rc.id, referrer_user_id=rc.user_id, referee_user_id=referee_user_id,
        credits_each=reward,
    ))
    await db.commit()
    logger.info("Referral redeemed: code=%s referrer=%s referee=%s", rc.code, rc.user_id, referee_user_id)
    return {
        "granted_credits": reward,
        "balance": await ent.credit_balance(db, referee_user_id),
    }


async def stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    rc = await get_or_create_code(db, user_id)
    n = await db.scalar(
        select(func.count()).select_from(ReferralRedemption).where(
            ReferralRedemption.referrer_user_id == user_id
        )
    ) or 0
    await db.commit()
    return {
        "code": rc.code,
        "share_base": settings.share_base_url,
        "referrals": int(n),
        "credits_earned": int(n) * settings.referral_reward_credits,
        "reward_credits": settings.referral_reward_credits,
    }


# ── Shareable anonymised result ──────────────────────────────────────────────

async def create_share(db: AsyncSession, assessment, owner_user_id: uuid.UUID) -> SharedResult:
    """Create (or reuse) a public, anonymised snapshot of an assessment's
    scores, stamped with the owner's referral code. No PII is copied."""
    existing = (
        await db.scalars(
            select(SharedResult).where(SharedResult.assessment_id == assessment.id)
        )
    ).first()
    if existing:
        return existing
    rc = await get_or_create_code(db, owner_user_id)
    share = SharedResult(
        token=secrets.token_urlsafe(18),
        assessment_id=assessment.id,
        owner_user_id=owner_user_id,
        traditional_score=assessment.traditional_score,
        semantic_score=assessment.semantic_score,
        capability_score=assessment.capability_score,
        score_delta=assessment.score_delta,
        counter_rec=bool(getattr(assessment, "counter_rec_triggered", False)),
        referral_code=rc.code,
    )
    db.add(share)
    await db.commit()
    return share


async def get_share(db: AsyncSession, token: str) -> dict | None:
    s = (await db.scalars(select(SharedResult).where(SharedResult.token == token))).first()
    if s is None:
        return None
    return {
        "traditional_score": s.traditional_score,
        "semantic_score": s.semantic_score,
        "capability_score": s.capability_score,
        "score_delta": s.score_delta,
        "counter_rec": s.counter_rec,
        "referral_code": s.referral_code,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }
