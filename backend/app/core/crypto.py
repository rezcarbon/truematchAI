"""Field-level encryption for PII at rest.

Provides AES-256-GCM authenticated encryption for sensitive columns and a keyed
blind-index (HMAC-SHA256) for fields that must remain searchable by equality
(e.g. the Singpass subject id) without storing them in the clear.

Design:
  * The data-encryption key (DEK) and blind-index key are base64-encoded and
    injected from a secrets manager / KMS at deploy time (settings.encryption_*).
  * Ciphertext tokens are self-describing: `enc:v1:<base64(nonce|ct|tag)>`. The
    version prefix allows key rotation and lets `decrypt` pass through legacy /
    dev plaintext unchanged (values without the prefix are returned as-is).
  * When no DEK is configured the app runs UNENCRYPTED (dev only) and logs a
    one-time warning; `encrypt` returns plaintext so the system stays runnable.

IP-SAFETY: no key material or plaintext is ever logged.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import logging
import os
from functools import lru_cache

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

logger = logging.getLogger("truematch.crypto")

_PREFIX = "enc:v1:"
_NONCE_BYTES = 12
# Stable, non-secret salt used only to derive a deterministic blind index in DEV
# (no index key configured). Never used when a real key is present.
_DEV_INDEX_SALT = b"truematch-dev-blind-index"

_warned = False


class CryptoError(RuntimeError):
    """Raised when decryption fails or an encrypted value cannot be read."""


def _b64decode(value: str) -> bytes:
    return base64.b64decode(value)


@lru_cache
def _dek() -> bytes | None:
    raw = settings.encryption_key.strip()
    if not raw:
        return None
    try:
        key = _b64decode(raw)
    except (binascii.Error, ValueError) as exc:
        raise CryptoError("encryption_key is not valid base64") from exc
    if len(key) != 32:
        raise CryptoError("encryption_key must decode to exactly 32 bytes (AES-256)")
    return key


@lru_cache
def _index_key() -> bytes:
    """Key for the blind index. Prefer an explicit index key; otherwise derive a
    distinct key from the DEK; in DEV (no keys) fall back to a fixed salt."""
    explicit = settings.encryption_index_key.strip()
    if explicit:
        return _b64decode(explicit)
    dek = _dek()
    if dek is not None:
        # Domain-separate from the DEK so the index key is not the raw DEK.
        return hashlib.sha256(b"blind-index:" + dek).digest()
    return _DEV_INDEX_SALT


def encryption_enabled() -> bool:
    return _dek() is not None


def _warn_once() -> None:
    global _warned
    if not _warned:
        logger.warning(
            "Field-level encryption is DISABLED (no encryption_key configured). "
            "PII is stored in plaintext — DEV ONLY. Configure encryption_key in production."
        )
        _warned = True


def encrypt(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    key = _dek()
    if key is None:
        _warn_once()
        return plaintext  # dev passthrough
    nonce = os.urandom(_NONCE_BYTES)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return _PREFIX + base64.b64encode(nonce + ct).decode("ascii")


def decrypt(token: str | None) -> str | None:
    if token is None:
        return None
    if not token.startswith(_PREFIX):
        # Legacy/dev plaintext written while encryption was disabled.
        return token
    key = _dek()
    if key is None:
        raise CryptoError("Encountered encrypted value but no encryption_key is configured")
    try:
        blob = base64.b64decode(token[len(_PREFIX):])
        nonce, ct = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
        return AESGCM(key).decrypt(nonce, ct, None).decode("utf-8")
    except (InvalidTag, ValueError, binascii.Error) as exc:
        raise CryptoError("Failed to decrypt value (wrong key or corrupted data)") from exc


def blind_index(value: str | None) -> str | None:
    """Deterministic, keyed index for equality lookups on encrypted fields.

    Normalizes case so lookups are case-insensitive. Returns hex HMAC-SHA256.
    """
    if value is None:
        return None
    normalized = value.strip().lower().encode("utf-8")
    return hmac.new(_index_key(), normalized, hashlib.sha256).hexdigest()
