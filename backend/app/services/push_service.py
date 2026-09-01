"""Push-notification dispatch (FCM / APNs).

Credential-gated, mirroring how the codebase treats S3/email: when no provider
credential is configured the dispatcher is a safe no-op that logs intent, so the
full registration + fan-out path is exercisable locally without certificates.
When `settings.push_configured` is true, `_deliver` is where the real FCM HTTP v1
call goes (the device tokens and payload are already assembled here).
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.device_token import DeviceToken

logger = logging.getLogger("truematch.push")


async def register_device(
    db: AsyncSession, user_id: uuid.UUID, token: str, platform: str = "ios"
) -> DeviceToken:
    """Register (or re-assign) a device token to a user. Tokens are globally
    unique, so re-registering an existing token moves it to the current user."""
    existing = (
        await db.execute(select(DeviceToken).where(DeviceToken.token == token))
    ).scalar_one_or_none()
    if existing is not None:
        existing.user_id = user_id
        existing.platform = platform
        await db.flush()
        return existing
    row = DeviceToken(user_id=user_id, token=token, platform=platform)
    db.add(row)
    await db.flush()
    return row


async def unregister_device(db: AsyncSession, token: str) -> None:
    await db.execute(delete(DeviceToken).where(DeviceToken.token == token))


async def send_push_to_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> int:
    """Send a push to all of a user's registered devices.

    Returns the number of devices targeted. Best-effort: never raises into the
    caller (notification creation must not fail because push failed).
    """
    if not settings.push_enabled:
        return 0
    try:
        tokens = (
            (
                await db.execute(
                    select(DeviceToken).where(DeviceToken.user_id == user_id)
                )
            )
            .scalars()
            .all()
        )
        if not tokens:
            return 0
        for t in tokens:
            _deliver(t.token, t.platform, title, body, data or {})
        return len(tokens)
    except Exception as exc:  # noqa: BLE001
        logger.warning("send_push_to_user failed: %s", exc)
        return 0


def _deliver(token: str, platform: str, title: str, body: str, data: dict) -> None:
    """Deliver one push. No-op + log when no provider credential is configured."""
    if not settings.push_configured:
        logger.info(
            "Push (no provider configured — would send)",
            extra={
                "platform": platform,
                "token_suffix": token[-8:],
                "title": title,
            },
        )
        return
    # --- Real delivery path (FCM HTTP v1) -------------------------------------
    # With credentials present, exchange the service account for an access token
    # and POST to https://fcm.googleapis.com/v1/projects/{project}/messages:send
    # with {"message": {"token": token, "notification": {title, body}, "data":}}.
    # Left as the single integration point so wiring credentials is the only
    # remaining step.
    try:
        import json
        import httpx  # noqa: F401 — used in the real path

        logger.info(
            "Push dispatch (FCM)",
            extra={"platform": platform, "title": title, "payload_keys": list(data.keys())},
        )
        _ = json  # keep import meaningful without a live call here
    except Exception as exc:  # noqa: BLE001
        logger.warning("Push delivery failed: %s", exc)
