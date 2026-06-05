"""Singpass OIDC helper tests (A3) — deterministic parts, no NDI network."""
from __future__ import annotations

import base64
import hashlib

import pytest

from app.core import oauth_state, singpass


def test_pkce_challenge_is_s256_of_verifier():
    verifier, challenge = singpass.generate_pkce()
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    assert challenge == expected


def test_parse_subject_extracts_uuid_not_nric():
    claims = {"sub": "s=S1234567A,u=a1b2c3d4-0000-1111-2222-333344445555"}
    assert singpass.parse_subject(claims) == "a1b2c3d4-0000-1111-2222-333344445555"


def test_parse_subject_rejects_nric_only():
    with pytest.raises(singpass.SingpassError):
        singpass.parse_subject({"sub": "s=S1234567A"})


def test_dev_identity_is_deterministic_and_uuid_shaped():
    a = singpass.dev_identity("code-abc", "nonce1")
    b = singpass.dev_identity("code-abc", "nonce2")
    assert a.singpass_id == b.singpass_id  # depends only on code
    assert a.singpass_id.startswith("dev-")
    # subject in claims never contains an NRIC component
    assert "s=" not in a.claims["sub"]


def test_build_auth_request_dev_mode_round_trips_state():
    # Not configured -> dev auth url points at our callback and carries state+code
    req = singpass.build_auth_request()
    assert req.state in req.auth_url
    assert "code=" in req.auth_url
    assert req.nonce and req.code_verifier


@pytest.mark.asyncio
async def test_oauth_state_is_single_use():
    req = singpass.build_auth_request()
    await oauth_state.put(req.state, {"nonce": req.nonce, "code_verifier": req.code_verifier})
    first = await oauth_state.pop(req.state)
    assert first is not None
    assert first["nonce"] == req.nonce
    # second pop must fail — state cannot be replayed
    second = await oauth_state.pop(req.state)
    assert second is None


def test_not_configured_in_dev():
    assert singpass.is_configured() is False
