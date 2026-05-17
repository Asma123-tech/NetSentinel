# app/security/auth.py
# ============================================================
# MODULE 4 — SECURE AUTHENTICATION & SESSION MANAGEMENT
# Protects against: Session Hijacking, Account Takeover,
#                   Credential Stuffing, Weak Passwords
# ============================================================

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import base64

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models

logger = logging.getLogger(__name__)

# ── JWT Configuration ─────────────────────────────────────────
# IMPORTANT: In production, set SECRET_KEY as an environment variable.
# Never hard-code a secret in production code.
SECRET_KEY      = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_ENV_VAR")
ALGORITHM       = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES  = 30    # short-lived access token
REFRESH_TOKEN_EXPIRE_DAYS    = 7     # longer-lived refresh token

# ── Password hashing (bcrypt) ─────────────────────────────────
# bcrypt automatically salts each hash — no need to store a separate salt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAuth2 scheme — reads Bearer token from Authorization header ──
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─────────────────────────────────────────────────────────────
# Password utilities
# ─────────────────────────────────────────────────────────────
def _prepare_password(plain_password: str) -> str:
    """
    bcrypt has a hard 72-byte limit. SHA-256 + base64 encoding
    keeps any password within 44 bytes while preserving full entropy.
    """
    digest = hashlib.sha256(plain_password.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("utf-8")

def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    bcrypt is resistant to brute-force due to its cost factor.
    """
    return pwd_context.hash(_prepare_password(plain_password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored bcrypt hash."""
    return pwd_context.verify(_prepare_password(plain_password), hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Enforce strong password policy.
    Rules:
      - Minimum 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, "OK"


# ─────────────────────────────────────────────────────────────
# JWT Token utilities
# ─────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.
    Payload includes: sub (user id), exp (expiry), type=access
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Create a signed JWT refresh token (longer-lived).
    Used to obtain a new access token without re-login.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    Raises HTTPException on invalid/expired tokens.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception


# ─────────────────────────────────────────────────────────────
# FastAPI dependency — get current authenticated user
# ─────────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    FastAPI dependency — validates the Bearer token and
    returns the User object from the database.

    Usage in any protected route:
        @router.get("/protected")
        def protected(user = Depends(get_current_user)):
            ...
    """
    payload = decode_token(token)

    # Ensure it's an access token (not a refresh token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = int(payload.get("sub"))
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Alias dependency — same as get_current_user but explicitly checks is_active."""
    return current_user
