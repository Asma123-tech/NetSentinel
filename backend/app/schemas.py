"""
Pydantic schemas for request validation and response serialisation.

CHANGE LOG:
  - UserCreate: added optional `full_name` field.
  - UserResponse: added optional `full_name` field.
  - All other schemas are unchanged.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ── Auth / User ────────────────────────────────────────────────

class UserCreate(BaseModel):
    username  : str       = Field(..., min_length=3, max_length=50)
    email     : EmailStr
    password  : str       = Field(..., min_length=8)
    full_name : Optional[str] = Field(None, max_length=100)   # ← NEW

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username may only contain letters, numbers, and underscores"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("one lowercase letter")
        if not re.search(r"[0-9]", v):
            errors.append("one number")
        if not re.search(r"[^A-Za-z0-9]", v):
            errors.append("one special character")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v


class UserResponse(BaseModel):
    id        : int
    username  : str
    email     : str
    full_name : Optional[str] = None    # ← NEW
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token : str
    refresh_token: str
    token_type   : str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Search ─────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query      : str  = Field(..., min_length=1, max_length=500)
    limit      : int  = Field(default=20, ge=1, le=500)
    filter_mode: Optional[str] = None


class SearchResultResponse(BaseModel):
    id         : int
    title      : str
    url        : str
    snippet    : Optional[str] = None
    type       : Optional[str] = None
    timestamp  : Optional[datetime] = None
    preview_url: Optional[str] = None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    results : List[SearchResultResponse]
    has_more: bool
    total   : int


# ── Settings ───────────────────────────────────────────────────

class SettingsResponse(BaseModel):
    filter_mode        : str
    parental_controls  : bool
    notifications      : bool
    save_search_history: bool
    blocked_keywords   : str
    allowed_domains    : str

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    filter_mode        : Optional[str]  = None
    parental_controls  : Optional[bool] = None
    notifications      : Optional[bool] = None
    save_search_history: Optional[bool] = None
    blocked_keywords   : Optional[str]  = None
    allowed_domains    : Optional[str]  = None


# ── Stats ───────────────────────────────────────────────────────

class OverviewStats(BaseModel):
    total_searches  : int
    blocked_content : int
    safe_results    : int
    active_time_hours: float


class ActivityItem(BaseModel):
    id             : int
    query          : str
    created_at     : datetime
    safe_results   : int
    blocked_results: int

    model_config = {"from_attributes": True}


# ── Security ────────────────────────────────────────────────────

class SecurityEventResponse(BaseModel):
    id        : int
    event_type: str
    severity  : str
    ip_address: Optional[str] = None
    details   : Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
    # Backwards-compatibility aliases — routers use these original names
SettingsOut    = SettingsResponse
SearchResultOut = SearchResultResponse
