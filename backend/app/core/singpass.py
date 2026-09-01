"""Singpass (Singapore NDI) OpenID Connect client.

Implements the production OIDC flow:
  1. Authorization request with PKCE (S256), `state`, and `nonce`.
  2. Token exchange using `private_key_jwt` client authentication.
  3. ID-token handling: JWE decryption (our private key) -> JWS verification
     against the Singpass JWKS -> claim checks (iss / aud / exp / nonce).
  4. Stable subject extraction (the NDI `u=` UUID), avoiding storage of the NRIC.

When NDI credentials are not configured (`settings.singpass_configured` is
False) the module operates in a bounded DEV mode that returns a deterministic
identity without any network call — so the end-to-end flow stays runnable and
testable. Production MUST configure real NDI credentials.

IP-SAFETY / PRIVACY: the raw NRIC (`s=` component of the subject) is never
returned or stored; only the opaque NDI UUID is used as `singpass_id`.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import jwe, jwt

from app.config import settings

logger = logging.getLogger("truematch.singpass")


class SingpassError(RuntimeError):
    """Raised when the Singpass OIDC flow cannot be completed."""


@dataclass(frozen=True)
class AuthRequest:
    auth_url: str
    state: str
    nonce: str
    code_verifier: str


@dataclass(frozen=True)
class Identity:
    singpass_id: str
    claims: dict[str, Any]


def is_configured() -> bool:
    return settings.singpass_configured


# --- PKCE -------------------------------------------------------------------

def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for the S256 PKCE method."""
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


# --- Discovery / keys -------------------------------------------------------

@lru_cache
def _load_jwk(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _discovery() -> dict[str, Any]:
    url = settings.singpass_issuer.rstrip("/") + "/.well-known/openid-configuration"
    resp = httpx.get(url, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


def _singpass_jwks() -> dict[str, Any]:
    jwks_uri = _discovery()["jwks_uri"]
    resp = httpx.get(jwks_uri, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


# --- Authorization request --------------------------------------------------

def build_auth_request() -> AuthRequest:
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    verifier, challenge = generate_pkce()

    if not is_configured():
        # DEV mode: point at our own callback so the round-trip is demonstrable.
        auth_url = (
            f"{settings.singpass_redirect_uri}?dev=1&state={state}&code=dev-{state[:8]}"
        )
        return AuthRequest(auth_url=auth_url, state=state, nonce=nonce, code_verifier=verifier)

    authorize_endpoint = _discovery()["authorization_endpoint"]
    params = {
        "response_type": "code",
        "client_id": settings.singpass_client_id,
        "redirect_uri": settings.singpass_redirect_uri,
        "scope": settings.singpass_scopes,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{authorize_endpoint}?{urlencode(params)}"
    return AuthRequest(auth_url=auth_url, state=state, nonce=nonce, code_verifier=verifier)


# --- Token exchange ---------------------------------------------------------

def _client_assertion(token_endpoint: str) -> str:
    """Build a private_key_jwt client assertion signed with our signing JWK."""
    sig_jwk = _load_jwk(settings.singpass_sig_jwk_path)
    now = int(time.time())
    claims = {
        "iss": settings.singpass_client_id,
        "sub": settings.singpass_client_id,
        "aud": token_endpoint,
        "iat": now,
        "exp": now + 120,
        "jti": secrets.token_urlsafe(16),
    }
    headers = {"kid": sig_jwk.get("kid")} if sig_jwk.get("kid") else None
    return jwt.encode(claims, sig_jwk, algorithm="ES256", headers=headers)


async def exchange_code(code: str, code_verifier: str) -> dict[str, Any]:
    token_endpoint = _discovery()["token_endpoint"]
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.singpass_redirect_uri,
        "client_id": settings.singpass_client_id,
        "code_verifier": code_verifier,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": _client_assertion(token_endpoint),
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise SingpassError(f"Token exchange failed ({resp.status_code}).")
    return resp.json()


# --- ID token handling ------------------------------------------------------

def decode_id_token(id_token: str, expected_nonce: str) -> dict[str, Any]:
    """Decrypt (JWE) then verify (JWS) the ID token and validate core claims."""
    enc_jwk = _load_jwk(settings.singpass_enc_jwk_path)
    try:
        # NDI ID tokens are JWE-wrapped; decrypt to recover the inner JWS.
        inner = jwe.decrypt(id_token, json.dumps(enc_jwk))
        if inner is None:
            raise SingpassError("ID token decryption returned empty payload.")
        signed_jwt = inner.decode("utf-8") if isinstance(inner, bytes) else inner
    except SingpassError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise SingpassError("ID token could not be decrypted.") from exc

    try:
        claims = jwt.decode(
            signed_jwt,
            _singpass_jwks(),
            algorithms=["ES256"],
            audience=settings.singpass_client_id,
            issuer=settings.singpass_issuer,
        )
    except Exception as exc:  # noqa: BLE001
        raise SingpassError("ID token signature/claims verification failed.") from exc

    if claims.get("nonce") != expected_nonce:
        raise SingpassError("ID token nonce mismatch.")
    return claims


def parse_subject(claims: dict[str, Any]) -> str:
    """Extract the stable, privacy-preserving subject identifier.

    NDI `sub` looks like `s=S1234567A,u=<uuid>`. We use the `u=` UUID and never
    retain the `s=` NRIC component.
    """
    sub = claims.get("sub", "")
    parts = dict(
        seg.split("=", 1) for seg in sub.split(",") if "=" in seg
    )
    uid = parts.get("u")
    if uid:
        return uid
    if sub and "s=" not in sub:
        return sub
    raise SingpassError("Subject identifier missing the NDI UUID component.")


# --- Dev fallback -----------------------------------------------------------

def dev_identity(code: str, nonce: str) -> Identity:
    """Deterministic identity for DEV mode (no NDI configured)."""
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]
    singpass_id = f"dev-{digest}"
    return Identity(
        singpass_id=singpass_id,
        claims={"sub": f"u={singpass_id}", "nonce": nonce, "_dev": True},
    )
