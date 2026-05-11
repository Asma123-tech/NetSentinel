# app/routers/auth.py
# ============================================================
# MODULE 4 — AUTH ROUTER
# Endpoints: POST /api/auth/signup, /api/auth/login, /api/auth/refresh, /api/auth/me
# ============================================================

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..security.auth import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
)
from ..security.rate_limiter import auth_rate_limit
from ..security.audit_logger import log_security_event, EventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


# ── Pydantic schemas (local to auth) ─────────────────────────

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True


# ── POST /api/auth/signup ─────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(
    payload: SignupRequest,
    request: Request,
    db: Session = Depends(get_db),
    _rl=Depends(auth_rate_limit),         # Module 3: rate limiting
):
    """
    Register a new user.
    - Validates password strength
    - Hashes password with bcrypt (never stored in plaintext)
    - Returns JWT access + refresh tokens
    """
    # Password strength check (Module 4)
    ok, reason = validate_password_strength(payload.password)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    # Check username uniqueness
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    # Check email uniqueness
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user with hashed password
    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    log_security_event(db, EventType.SIGNUP_SUCCESS, request, user_id=user.id,
                       details=f"New user registered: {user.username}")

    access_token  = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── POST /api/auth/login ──────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _rl=Depends(auth_rate_limit),         # Module 3: stricter rate limit on login
):
    """
    Authenticate user with username + password.
    - Rate-limited to prevent brute-force
    - Returns short-lived access token + refresh token
    - Uses constant-time comparison via bcrypt to prevent timing attacks
    """
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()

    # Always verify (even if user not found) to prevent timing oracle
    dummy_hash = "$2b$12$KIXcaIBuFGiHqnDMeILhiOKlh5WJYkW0u3mTSoFj8Aol/q7OEIBW6"
    stored_hash = user.hashed_password if user else dummy_hash

    if not verify_password(form_data.password, stored_hash) or user is None:
        log_security_event(db, EventType.LOGIN_FAILED, request,
                           details=f"Failed login for username: {form_data.username!r}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    log_security_event(db, EventType.LOGIN_SUCCESS, request, user_id=user.id,
                       details=f"Login: {user.username}")

    access_token  = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── POST /api/auth/refresh ────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    Allows sessions to stay alive without re-logging in.
    """
    token_data = decode_token(payload.refresh_token)

    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")

    user_id = int(token_data.get("sub"))
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_access  = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


# ── GET /api/auth/me ──────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def get_me(current_user: models.User = Depends(get_current_active_user)):
    """Return the currently authenticated user's profile."""
    return current_user
