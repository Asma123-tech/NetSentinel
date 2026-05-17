"""
Database models for NetSentinel.

CHANGE LOG:
  - User: added `full_name` column (nullable String, non-breaking for existing rows).
    Run the migration SQL after deploying this file:
      ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(100);
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


# ── User ───────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50),  unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    full_name       = Column(String(100), nullable=True)          # ← NEW (nullable)
    hashed_password = Column(String(255), nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships — keep exactly as they were in your original file
    search_queries  = relationship("SearchQuery",   back_populates="user", cascade="all, delete-orphan")
    settings        = relationship("UserSettings",  back_populates="user", uselist=False, cascade="all, delete-orphan")
    security_events = relationship("SecurityEvent", back_populates="user", cascade="all, delete-orphan")


# ── SearchQuery ────────────────────────────────────────────────

class SearchQuery(Base):
    __tablename__ = "search_queries"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    query      = Column(String(500), nullable=False)
    filter_mode= Column(String(20),  nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user    = relationship("User",         back_populates="search_queries")
    results = relationship("SearchResult", back_populates="query", cascade="all, delete-orphan")


# ── SearchResult ───────────────────────────────────────────────

class SearchResult(Base):
    __tablename__ = "search_results"

    id          = Column(Integer, primary_key=True, index=True)
    query_id    = Column(Integer, ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False)
    title       = Column(String(500), nullable=False)
    url         = Column(Text,        nullable=False)
    snippet     = Column(Text,        nullable=True)
    result_type = Column(String(20),  nullable=True)
    preview_url = Column(Text,        nullable=True)
    is_blocked  = Column(Boolean,     default=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    query = relationship("SearchQuery", back_populates="results")


# ── GlobalSettings (kept for backwards compatibility) ──────────

# In models.py — inside the GlobalSettings class, add this property:
class GlobalSettings(Base):
    __tablename__ = "global_settings"

    id                = Column(Integer, primary_key=True, index=True)
    filter_mode       = Column(String(20), default="strict")
    parental_controls = Column(Boolean,    default=True)
    notifications     = Column(Boolean,    default=True)
    save_history      = Column(Boolean,    default=True)   # ← actual column name
    blocked_keywords  = Column(Text,       default="")
    allowed_domains   = Column(Text,       default="")
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def save_search_history(self) -> bool:          # ← bridge property
        return self.save_history

    @save_search_history.setter
    def save_search_history(self, value: bool):
        self.save_history = value


# ── UserSettings (per-user settings) ──────────────────────────

class UserSettings(Base):
    __tablename__ = "user_settings"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    filter_mode         = Column(String(20), default="strict")
    parental_controls   = Column(Boolean,    default=True)
    notifications       = Column(Boolean,    default=True)
    save_search_history = Column(Boolean,    default=True)
    blocked_keywords    = Column(Text,       default="")
    allowed_domains     = Column(Text,       default="")
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="settings")


# ── SecurityEvent ──────────────────────────────────────────────

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False)
    severity   = Column(String(20),  nullable=False, default="INFO")
    ip_address = Column(String(45),  nullable=True)
    details    = Column(Text,        nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="security_events")