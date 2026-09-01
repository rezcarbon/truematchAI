"""Encryption configuration and deterministic encryption support.

This module provides:
  * EncryptionMode enum for 'full' (AES-256-GCM) and 'deterministic' (HMAC-SHA256)
  * EncryptionKeyInfo model for managing encryption keys and metadata
  * Field-level encryption mode and queryability configuration
  * Deterministic encryption using HMAC-SHA256 for searchable/queryable fields
  * Integration with the existing app/core/crypto.py patterns

Design:
  * Queryable fields (status, governance_status, assessment_status) use deterministic
    encryption via HMAC-SHA256, producing the same hash for the same input (enables EQ queries).
  * Narrative/sensitive fields use full encryption (AES-256-GCM, irreversible in normal flow).
  * The EncryptionKeyInfo tracks key versions, active status, and rotation dates for
    key rotation support.
  * Field encryption modes are declaratively defined, not scattered through business logic.

IP-SAFETY: No key material or plaintext is ever logged.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache

from pydantic import BaseModel, Field

from app.core import crypto

logger = logging.getLogger("truematch.encryption_config")

# ─────────────────────────────────────────────────────────────────────────────
# ENUMS AND TYPES
# ─────────────────────────────────────────────────────────────────────────────


class EncryptionMode(str, Enum):
    """Encryption mode for sensitive fields.

    FULL: Irreversible encryption using AES-256-GCM. Ciphertext is unique per
          encryption (nonce is randomized), so same plaintext produces different
          ciphertexts. Cannot be queried by value.

    DETERMINISTIC: Keyed HMAC-SHA256 producing same hash for same input. Enables
                   equality (=) queries on encrypted fields without decryption.
                   Not reversible (by design) — suitable for status codes and
                   categorical values only.
    """

    FULL = "full"
    DETERMINISTIC = "deterministic"


# ─────────────────────────────────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────────────────────────────────


class EncryptionKeyInfo(BaseModel):
    """Metadata and key material for an encryption key version.

    Attributes:
        version: Unique version identifier for this key (increments on rotation).
        key: 32-byte AES-256 key for full encryption. May be None if encryption
             is disabled (dev mode).
        hmac_key: 32-byte HMAC-SHA256 key for deterministic encryption. Derived
                  from the main key if not explicitly set (matching crypto.py behavior).
                  May be None if encryption is disabled.
        rotation_date: UTC timestamp when this key was rotated in.
        is_active: Whether this key is currently active for encryption. During
                   rotation, old keys remain is_active=False for decryption-only.
    """

    version: int
    key: bytes | None = Field(default=None, exclude=True)
    hmac_key: bytes | None = Field(default=None, exclude=True)
    rotation_date: datetime
    is_active: bool

    model_config = {
        "json_encoders": {
            bytes: lambda v: "[redacted]" if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        }
    }

    def __repr__(self) -> str:
        """Safe repr that does not expose key material."""
        return (
            f"EncryptionKeyInfo(version={self.version}, "
            f"active={self.is_active}, "
            f"rotation_date={self.rotation_date.isoformat()})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# KEY MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_active_encryption_key() -> EncryptionKeyInfo:
    """Get the currently active encryption key for new encryptions.

    Returns:
        EncryptionKeyInfo with the active key, version, and metadata. The key
        is populated from the configured settings (encryption_key, encryption_index_key).

    Note:
        If encryption is disabled (dev mode), this returns a key with None values.
        The caller must check is_active or key is not None before using it.

    Raises:
        Logs a warning if encryption is disabled but queried.
    """
    # Get the DEK and index key from the existing crypto module
    dek = crypto._dek()  # type: ignore
    index_key = crypto._index_key()  # type: ignore

    # If no DEK is configured, return a disabled key info
    if dek is None:
        logger.debug("Encryption disabled (no encryption_key configured)")
        return EncryptionKeyInfo(
            version=0,
            key=None,
            hmac_key=None,
            rotation_date=datetime.now(timezone.utc),
            is_active=False,
        )

    # Return the active key info with current versions
    return EncryptionKeyInfo(
        version=1,  # Default version; can be incremented per deployment/rotation
        key=dek,
        hmac_key=index_key,
        rotation_date=datetime.now(timezone.utc),
        is_active=True,
    )


def is_encryption_enabled() -> bool:
    """Check if field-level encryption is currently enabled.

    Returns:
        True if an encryption key is configured, False otherwise.
    """
    return crypto.encryption_enabled()


# ─────────────────────────────────────────────────────────────────────────────
# FIELD CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Map of field names to their queryability status.
# Queryable fields can be searched by equality without decryption;
# non-queryable (narrative) fields are encrypted irreversibly.
_QUERYABLE_FIELDS = {
    "status",
    "governance_status",
    "assessment_status",
    "match_status",
    "stage",
}

_SENSITIVE_FIELDS = {
    "capability_narrative",
    "counter_rec_reasoning",
    "assessment_notes",
    "evaluation_rationale",
}


def is_field_queryable(field_name: str) -> bool:
    """Check if a field is queryable (can be searched by equality).

    Queryable fields use deterministic encryption (HMAC-SHA256) so the same
    plaintext always produces the same ciphertext, enabling = queries.

    Args:
        field_name: The field name to check.

    Returns:
        True if the field is in the queryable set, False otherwise.
    """
    return field_name.lower() in _QUERYABLE_FIELDS


def get_field_encryption_mode(field_name: str) -> EncryptionMode:
    """Determine the encryption mode for a given field.

    Args:
        field_name: The field name to check.

    Returns:
        EncryptionMode.DETERMINISTIC for queryable fields (status, governance_status, etc.)
        EncryptionMode.FULL for sensitive/narrative fields (capability_narrative, etc.)

    Note:
        If a field is not explicitly configured, it defaults to FULL encryption.
        Use this to make encryption decisions at the ORM/schema level.
    """
    if is_field_queryable(field_name):
        return EncryptionMode.DETERMINISTIC
    return EncryptionMode.FULL


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC ENCRYPTION (HMAC-SHA256)
# ─────────────────────────────────────────────────────────────────────────────


def deterministic_encrypt(value: str, hmac_key: bytes) -> str:
    """Encrypt a value deterministically using HMAC-SHA256.

    Produces a cryptographic hash of the plaintext that is:
      * Deterministic: same input always produces the same output (enables queries)
      * Keyed: requires the HMAC key to compute, prevents plaintext brute-force
      * Non-reversible: the hash cannot be inverted to recover the plaintext

    Use this for status codes, categorical values, and any field that must be
    searchable by equality (WHERE status = 'APPROVED') without storing plaintext.

    Args:
        value: The plaintext to hash. Non-None strings only.
        hmac_key: The 32-byte HMAC-SHA256 key.

    Returns:
        Hex-encoded HMAC-SHA256 digest (64 hex characters).

    Raises:
        ValueError: If value is None or hmac_key is invalid.
    """
    if value is None:
        raise ValueError("Cannot encrypt None value with deterministic_encrypt")
    if not hmac_key or len(hmac_key) < 16:
        raise ValueError("hmac_key must be at least 16 bytes")

    normalized = value.strip().lower().encode("utf-8")
    digest = hmac.new(hmac_key, normalized, hashlib.sha256).hexdigest()
    return digest


def deterministic_encrypt_optional(value: str | None, hmac_key: bytes) -> str | None:
    """Encrypt a value deterministically, or return None if value is None.

    Args:
        value: The plaintext to hash, or None.
        hmac_key: The 32-byte HMAC-SHA256 key.

    Returns:
        Hex-encoded HMAC-SHA256 digest, or None if value is None.
    """
    if value is None:
        return None
    return deterministic_encrypt(value, hmac_key)


def deterministic_decrypt() -> None:
    """Stub: deterministic encryption is not reversible by design.

    Deterministic HMAC-based encryption cannot be decrypted. Once a value is
    hashed with deterministic_encrypt, recovery of the plaintext is not possible.

    If you need to store and later retrieve the plaintext, use full encryption
    (AES-256-GCM via crypto.encrypt/crypto.decrypt) instead.

    Raises:
        NotImplementedError: Always. This operation is not supported.
    """
    raise NotImplementedError(
        "Deterministic encryption cannot be decrypted. "
        "Use crypto.decrypt() for full encryption, or store plaintext elsewhere "
        "if decryption is required."
    )


# ─────────────────────────────────────────────────────────────────────────────
# FULL ENCRYPTION WRAPPERS
# ─────────────────────────────────────────────────────────────────────────────

def full_encrypt(plaintext: str | None) -> str | None:
    """Encrypt a value using full AES-256-GCM encryption.

    Delegates to crypto.encrypt(). Produces unique ciphertext per call (nonce
    is randomized), so the same plaintext encrypts to different ciphertexts.
    Cannot be queried without decryption.

    Args:
        plaintext: The plaintext to encrypt, or None.

    Returns:
        Encrypted ciphertext (base64-encoded, prefixed with "enc:v1:"), or None.

    Note:
        If encryption is disabled (dev mode), returns plaintext unchanged and
        logs a one-time warning.
    """
    return crypto.encrypt(plaintext)


def full_decrypt(token: str | None) -> str | None:
    """Decrypt a full-encryption ciphertext using AES-256-GCM.

    Delegates to crypto.decrypt(). Handles legacy plaintext (returns unchanged),
    validates the ciphertext format, and raises CryptoError on decryption failure.

    Args:
        token: The encrypted token (or plaintext, for legacy compatibility), or None.

    Returns:
        Decrypted plaintext, or None.

    Raises:
        crypto.CryptoError: If the ciphertext is invalid or decryption fails.
    """
    return crypto.decrypt(token)


def full_encrypt_with_blind_index(plaintext: str | None) -> tuple[str | None, str | None]:
    """Encrypt a value with full encryption AND generate a deterministic blind index.

    Useful for fields that need both privacy (full encryption) and queryability
    (blind index for equality searches). Store both the ciphertext and the index,
    then query by the index without touching the encrypted data.

    Args:
        plaintext: The plaintext to encrypt, or None.

    Returns:
        Tuple of (ciphertext, blind_index). Both may be None if plaintext is None.
    """
    ciphertext = full_encrypt(plaintext)
    index = crypto.blind_index(plaintext)
    return ciphertext, index


# ─────────────────────────────────────────────────────────────────────────────
# HIGH-LEVEL ENCRYPTION DECISION
# ─────────────────────────────────────────────────────────────────────────────


def encrypt_field(field_name: str, value: str | None) -> str | None:
    """Encrypt a field value using the appropriate mode for that field.

    This is the primary entry point for field-level encryption. It determines
    the encryption mode based on field_name, then applies the appropriate
    encryption strategy.

    Args:
        field_name: The name of the field being encrypted.
        value: The plaintext value, or None.

    Returns:
        Encrypted value (format depends on encryption mode), or None.

    Note:
        * Queryable fields (status, governance_status, etc.) use deterministic
          encryption (returns HMAC digest as hex string).
        * Sensitive fields (capability_narrative, etc.) use full encryption
          (returns AES-256-GCM ciphertext).
        * If encryption is disabled, returns plaintext.
    """
    if value is None:
        return None

    mode = get_field_encryption_mode(field_name)

    if mode == EncryptionMode.DETERMINISTIC:
        key_info = get_active_encryption_key()
        if not key_info.is_active or key_info.hmac_key is None:
            logger.warning(
                f"Field {field_name} requires deterministic encryption but no key is active"
            )
            return value  # Fallback to plaintext in dev
        return deterministic_encrypt(value, key_info.hmac_key)
    else:  # EncryptionMode.FULL
        return full_encrypt(value)


def decrypt_field(field_name: str, encrypted_value: str | None) -> str | None:
    """Decrypt a field value using the appropriate mode for that field.

    This is the primary entry point for field-level decryption. It determines
    the encryption mode based on field_name, then applies the appropriate
    decryption strategy.

    Args:
        field_name: The name of the field being decrypted.
        encrypted_value: The encrypted value (format depends on encryption mode), or None.

    Returns:
        Decrypted plaintext, or None.

    Note:
        * Queryable fields (deterministic) cannot be meaningfully decrypted
          (HMAC is one-way). This function returns the hash unchanged.
        * Sensitive fields (full encryption) are decrypted via AES-256-GCM.
        * Legacy plaintext (unencrypted values) are returned unchanged.

    Raises:
        crypto.CryptoError: If full decryption fails.
    """
    if encrypted_value is None:
        return None

    mode = get_field_encryption_mode(field_name)

    if mode == EncryptionMode.DETERMINISTIC:
        # Deterministic hashes cannot be reversed. Return the hash unchanged.
        # (In practice, application code should not attempt to decrypt these.)
        logger.debug(
            f"Attempted to decrypt deterministic field {field_name}; returning value unchanged"
        )
        return encrypted_value
    else:  # EncryptionMode.FULL
        return full_decrypt(encrypted_value)
