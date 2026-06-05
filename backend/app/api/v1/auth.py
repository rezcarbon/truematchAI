"""Auth endpoints: signup, login, refresh, session logout, Singpass OIDC."""
from __future__ import annotations

import logging

from fastapi import APIRouter, status
from sqlalchemy import select

from app.core import oauth_state, singpass
from app.core.crypto import blind_index
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.deps import CurrentUser, DBSession
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    SignupRequest,
    SingpassCallbackRequest,
    SingpassInitResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter()
logger = logging.getLogger("truematch.auth")


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: DBSession) -> TokenResponse:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise ConflictError("Email already registered", instance="/api/v1/auth/signup")

    # Hash password asynchronously to avoid blocking event loop
    password_hash = await hash_password(payload.password)

    user = User(
        email=payload.email,
        password_hash=password_hash,
        display_name=payload.display_name,
        role=payload.role,
        company_id=payload.company_id,
    )
    db.add(user)
    await db.flush()
    sub = str(user.id)
    return TokenResponse(
        access_token=create_access_token(sub, role=user.role.value),
        refresh_token=create_refresh_token(sub),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DBSession) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.password_hash or not verify_password(
        payload.password, user.password_hash
    ):
        raise AuthenticationError("Invalid credentials")
    sub = str(user.id)
    return TokenResponse(
        access_token=create_access_token(sub, role=user.role.value),
        refresh_token=create_refresh_token(sub),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: DBSession) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise AuthenticationError("Invalid refresh token")
    if data.get("type") != REFRESH_TOKEN_TYPE:
        raise AuthenticationError("Invalid token type")
    sub = data.get("sub")
    if not sub:
        raise AuthenticationError("Invalid token")
    return TokenResponse(
        access_token=create_access_token(sub),
        refresh_token=create_refresh_token(sub),
    )


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: CurrentUser) -> None:
    """Stateless JWT logout.

    With stateless JWTs the client discards its tokens. A production deployment
    would also add the token jti to a Redis denylist until expiry.
    """
    return None


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> User:
    return user


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChangeRequest, user: CurrentUser, db: DBSession
) -> None:
    """Change the current user's password.

    Requires verifying the current password before allowing change.
    Returns 204 No Content on success.
    """
    # Verify current password
    if not user.password_hash or not verify_password(
        payload.current_password, user.password_hash
    ):
        raise AuthenticationError("Current password is incorrect")

    # Hash new password and update
    user.password_hash = await hash_password(payload.new_password)
    await db.flush()
    logger.info(f"Password changed for user {user.id}")
    return None


# --- Singpass (Singapore NDI) OIDC ------------------------------------------

@router.get("/singpass/init", response_model=SingpassInitResponse)
async def singpass_init() -> SingpassInitResponse:
    """Begin a Singpass OIDC flow.

    Generates PKCE + state + nonce, stores the per-login secrets server-side
    keyed by `state`, and returns the authorization URL. Runs in DEV mode when
    NDI credentials are not configured.
    """
    req = singpass.build_auth_request()
    await oauth_state.put(
        req.state, {"nonce": req.nonce, "code_verifier": req.code_verifier}
    )
    return SingpassInitResponse(auth_url=req.auth_url, state=req.state)


@router.post("/singpass/callback", response_model=TokenResponse)
async def singpass_callback(payload: SingpassCallbackRequest, db: DBSession) -> TokenResponse:
    """Complete a Singpass OIDC flow and issue TrueMatch tokens.

    Validates the single-use `state`, exchanges the code (live), decrypts and
    verifies the ID token, and upserts the user by the privacy-preserving NDI
    UUID. In DEV mode (no NDI credentials) a deterministic identity is used.
    """
    stored = await oauth_state.pop(payload.state)
    if stored is None:
        # Unknown/expired/replayed state.
        raise AuthenticationError("Invalid or expired login state")

    nonce = stored["nonce"]
    code_verifier = stored["code_verifier"]

    try:
        if singpass.is_configured():
            tokens = await singpass.exchange_code(payload.code, code_verifier)
            id_token = tokens.get("id_token")
            if not id_token:
                raise singpass.SingpassError("Token response missing id_token.")
            claims = singpass.decode_id_token(id_token, expected_nonce=nonce)
            identity = singpass.Identity(
                singpass_id=singpass.parse_subject(claims), claims=claims
            )
        else:
            identity = singpass.dev_identity(payload.code, nonce)
    except singpass.SingpassError as exc:
        logger.warning("Singpass authentication failed: %s", exc)
        raise AuthenticationError("Singpass authentication failed") from exc

    # singpass_id is encrypted at rest; look it up via the keyed blind index.
    bidx = blind_index(identity.singpass_id)
    user = await db.scalar(select(User).where(User.singpass_id_bidx == bidx))
    if user is None:
        user = User(
            # NDI does not release email by default; use a stable internal handle.
            email=f"{identity.singpass_id}@singpass.local",
            singpass_id=identity.singpass_id,
            singpass_id_bidx=bidx,
            display_name="Singpass User",
        )
        db.add(user)
        await db.flush()

    sub = str(user.id)
    return TokenResponse(
        access_token=create_access_token(sub, role=user.role.value),
        refresh_token=create_refresh_token(sub),
    )
