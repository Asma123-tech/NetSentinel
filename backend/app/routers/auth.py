"""
Authentication router — /api/auth/*

Endpoints:
  POST /api/auth/signup   — create account
  POST /api/auth/login    — obtain JWT tokens
  POST /api/auth/refresh  — rotate access token
  GET  /api/auth/me       — return current user profile

CHANGE LOG:
  - signup: stores full_name when provided.
  - signup: returns explicit 409 errors for duplicate email / username.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token, RefreshRequest
from app.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Signup ─────────────────────────────────────────────────────

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    Returns access + refresh tokens immediately so the user is logged in.
    """
    # Check for duplicate email — explicit error so the frontend can show
    # "this email is already registered" rather than a generic 500.
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Check for duplicate username
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken. Please choose a different one.",
        )

    user = User(
        username        = payload.username,
        email           = payload.email,
        full_name       = payload.full_name,       # ← NEW
        hashed_password = hash_password(payload.password),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or username already exists.",
        )

    access_token  = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return Token(access_token=access_token, refresh_token=refresh_token)


# ── Login ──────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate with username + password (OAuth2 form-encoded body).
    Returns access + refresh tokens on success.
    """
    # Allow login with either username or email
    user = (
        db.query(User)
        .filter(
            (User.username == form_data.username) |
            (User.email == form_data.username)
        )
        .first()
    )

    # Use constant-time comparison to prevent timing attacks
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token  = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return Token(access_token=access_token, refresh_token=refresh_token)


# ── Refresh ────────────────────────────────────────────────────

@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Rotate the access token using a valid refresh token."""
    token_data = decode_token(payload.refresh_token)

    if not token_data or not token_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user = db.query(User).filter(User.username == token_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    new_access  = create_access_token({"sub": user.username})
    new_refresh = create_refresh_token({"sub": user.username})

    return Token(access_token=new_access, refresh_token=new_refresh)


# ── Me ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user