"""Token denylist management using Redis.

Provides a centralized mechanism to revoke JWT tokens before expiry.
Tokens are stored in Redis with their expiry time, allowing:
- Logout: revoke current token
- Revoke all user tokens: force re-login for a user
- Automatic cleanup: expired tokens are removed by Redis TTL
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Redis key prefix for token denylist entries
TOKEN_DENYLIST_PREFIX = "token_denylist:"
USER_TOKEN_PREFIX = "user_tokens:"


class TokenDenylist:
    """Manage revoked JWT tokens in Redis."""

    def __init__(self, redis_client: redis.Redis[bytes]) -> None:
        """Initialize token denylist with Redis client.

        Args:
            redis_client: redis.asyncio.Redis instance
        """
        self.redis = redis_client

    async def add_token_to_denylist(self, token_jti: str, expiry_seconds: int) -> None:
        """Add a token JTI to the denylist until its expiry time.

        The token is stored in Redis with an expiry equal to the token's
        remaining lifetime. When the token would expire naturally anyway,
        Redis automatically deletes it.

        Args:
            token_jti: The token's JTI (unique ID) claim
            expiry_seconds: Seconds until token naturally expires

        Raises:
            Exception: If Redis operation fails
        """
        key = f"{TOKEN_DENYLIST_PREFIX}{token_jti}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # Store the revocation timestamp, expire after the token's natural lifetime
            await self.redis.setex(
                key, expiry_seconds, timestamp.encode()
            )
            logger.debug(
                "Token added to denylist",
                extra={"token_jti": token_jti, "expiry_seconds": expiry_seconds},
            )
        except Exception as e:
            logger.error(
                "Failed to add token to denylist",
                extra={"token_jti": token_jti, "error": str(e)},
            )
            raise

    async def is_token_revoked(self, token_jti: str) -> bool:
        """Check if a token JTI is in the denylist.

        Args:
            token_jti: The token's JTI claim

        Returns:
            True if token is revoked, False otherwise

        Raises:
            Exception: If Redis operation fails
        """
        key = f"{TOKEN_DENYLIST_PREFIX}{token_jti}"

        try:
            exists = await self.redis.exists(key)
            if exists:
                logger.debug(
                    "Token found in denylist",
                    extra={"token_jti": token_jti},
                )
            return bool(exists)
        except Exception as e:
            logger.error(
                "Failed to check token denylist",
                extra={"token_jti": token_jti, "error": str(e)},
            )
            raise

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all tokens for a user.

        Finds all tokens associated with a user (by scanning user_token index)
        and removes them from the denylist. This forces the user to re-login.

        Args:
            user_id: UUID of the user

        Returns:
            Number of tokens revoked

        Raises:
            Exception: If Redis operation fails
        """
        user_key = f"{USER_TOKEN_PREFIX}{user_id}"

        try:
            # Get all tokens for this user
            token_jtis = await self.redis.smembers(user_key)
            revoked_count = 0

            for token_jti_bytes in token_jtis:
                token_jti = (
                    token_jti_bytes.decode() if isinstance(token_jti_bytes, bytes)
                    else token_jti_bytes
                )
                denylist_key = f"{TOKEN_DENYLIST_PREFIX}{token_jti}"
                await self.redis.delete(denylist_key)
                revoked_count += 1

            # Clean up the user token index
            await self.redis.delete(user_key)

            logger.info(
                "Revoked all tokens for user",
                extra={"user_id": str(user_id), "revoked_count": revoked_count},
            )
            return revoked_count

        except Exception as e:
            logger.error(
                "Failed to revoke all user tokens",
                extra={"user_id": str(user_id), "error": str(e)},
            )
            raise

    async def add_user_token(
        self, user_id: UUID, token_jti: str, expiry_seconds: int
    ) -> None:
        """Record a token as belonging to a user (for later revocation).

        Maintains a set of token JTIs per user, allowing revoke_all_user_tokens()
        to find and revoke all tokens for that user.

        Args:
            user_id: UUID of the user
            token_jti: The token's JTI claim
            expiry_seconds: Seconds until token expires

        Raises:
            Exception: If Redis operation fails
        """
        user_key = f"{USER_TOKEN_PREFIX}{user_id}"

        try:
            # Add to user's token set
            await self.redis.sadd(user_key, token_jti)
            # Set expiry on the user key (refresh on each token creation)
            await self.redis.expire(user_key, expiry_seconds)
            logger.debug(
                "Recorded user token",
                extra={"user_id": str(user_id), "token_jti": token_jti},
            )
        except Exception as e:
            logger.error(
                "Failed to record user token",
                extra={
                    "user_id": str(user_id),
                    "token_jti": token_jti,
                    "error": str(e),
                },
            )
            raise

    async def get_denylist_stats(self) -> dict[str, Any]:
        """Get statistics about the current denylist.

        Returns:
            Dictionary with denylist_size, user_token_indices, etc.

        Raises:
            Exception: If Redis operation fails
        """
        try:
            # Count denylist entries
            denylist_cursor = 0
            denylist_count = 0
            denylist_cursor, denylist_keys = await self.redis.scan(
                cursor=denylist_cursor, match=f"{TOKEN_DENYLIST_PREFIX}*", count=100
            )
            denylist_count = len(denylist_keys)

            # Count user token indices
            user_cursor = 0
            user_count = 0
            user_cursor, user_keys = await self.redis.scan(
                cursor=user_cursor, match=f"{USER_TOKEN_PREFIX}*", count=100
            )
            user_count = len(user_keys)

            return {
                "denylist_size": denylist_count,
                "user_token_indices": user_count,
            }
        except Exception as e:
            logger.error(
                "Failed to get denylist stats",
                extra={"error": str(e)},
            )
            return {"error": str(e)}


def get_token_denylist(redis_client: redis.Redis[bytes]) -> TokenDenylist:
    """Factory function to create a TokenDenylist instance.

    Args:
        redis_client: redis.asyncio.Redis instance

    Returns:
        TokenDenylist instance
    """
    return TokenDenylist(redis_client)


__all__ = ["TokenDenylist", "get_token_denylist", "TOKEN_DENYLIST_PREFIX"]
