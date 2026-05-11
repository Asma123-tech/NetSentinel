# app/models.py  — UPDATED (security modules added)
# New models: User (Module 4), SecurityEvent (Module 6)

from datetime import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, DateTime,
    Boolean, Enum, ForeignKey, Text,
)
from sqlalchemy.orm import relationship

from .database import Base


# ─── Existing enums (unchanged) ──────────────────────────────

class FilterMode(str, enum.Enum):
    strict   = "strict"
    moderate = "moderate"
    relaxed  = "relaxed"


class ResultType(str, enum.Enum):
    text  = "text"
    image = "image"
    video = "video"


# ─── Existing models (unchanged) ─────────────────────────────

class SearchQuery(Base):
    __tablename__ = "search_queries"

    id             = Column(Integer, primary_key=True, index=True)
    query          = Column(String(512), nullable=False)
    filter_mode    = Column(Enum(FilterMode), nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_results  = Column(Integer, default=0)
    safe_results   = Column(Integer, default=0)
    blocked_results = Column(Integer, default=0)

    results = relationship(
        "SearchResult",
        back_populates="search_query",
        cascade="all, delete-orphan",
    )


class SearchResult(Base):
    __tablename__ = "search_results"

    id             = Column(Integer, primary_key=True, index=True)
    query_id       = Column(Integer, ForeignKey("search_queries.id", ondelete="CASCADE"))
    title          = Column(String(512), nullable=False)
    url            = Column(String(1024), nullable=False)
    snippet        = Column(Text, nullable=False)
    type           = Column(Enum(ResultType), default=ResultType.text, nullable=False)
    is_blocked     = Column(Boolean, default=False)
    blocked_reason = Column(String(256), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)

    search_query = relationship("SearchQuery", back_populates="results")


class GlobalSettings(Base):
    __tablename__ = "global_settings"

    id                = Column(Integer, primary_key=True, index=True)
    filter_mode       = Column(Enum(FilterMode), default=FilterMode.relaxed, nullable=False)
    parental_controls = Column(Boolean, default=True)
    notifications     = Column(Boolean, default=True)
    save_search_history = Column(Boolean, default=True)
    blocked_keywords  = Column(Text, default="")
    allowed_domains   = Column(Text, default="")


# ─── MODULE 4: User model ─────────────────────────────────────

class User(Base):
    """
    Stores registered user accounts.
    Password is NEVER stored in plaintext — only bcrypt hash.
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(64), unique=True, nullable=False, index=True)
    email           = Column(String(256), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)   # bcrypt hash
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login      = Column(DateTime, nullable=True)


# ─── MODULE 6: SecurityEvent model ───────────────────────────

class SecurityEvent(Base):
    """
    Audit log table — every security-relevant event is written here.
    Powers the intrusion detection dashboard.

    Severity levels:
        INFO     — normal events (login, search)
        WARNING  — suspicious but not confirmed attack
        CRITICAL — confirmed attack attempt (SQLi, XSS, etc.)
    """
    __tablename__ = "security_events"

    id         = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(64),  nullable=False, index=True)
    severity   = Column(String(16),  nullable=False, index=True)  # INFO / WARNING / CRITICAL
    ip_address = Column(String(64),  nullable=False, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    path       = Column(String(512), nullable=False)
    method     = Column(String(10),  nullable=False)
    user_agent = Column(String(256), nullable=True)
    details    = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
