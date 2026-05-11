# app/security/audit_logger.py
# ============================================================
# MODULE 6 — AUDIT LOGGING & INTRUSION DETECTION
# Tracks: All security events, suspicious patterns, blocked
#         attacks, login attempts, rate limit violations
# ============================================================

import enum
import logging
from datetime import datetime
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from ..models import SecurityEvent   # we add this model in models.py

logger = logging.getLogger(__name__)


class EventType(str, enum.Enum):
    # Authentication events
    LOGIN_SUCCESS    = "LOGIN_SUCCESS"
    LOGIN_FAILED     = "LOGIN_FAILED"
    SIGNUP_SUCCESS   = "SIGNUP_SUCCESS"
    LOGOUT           = "LOGOUT"
    TOKEN_REFRESH    = "TOKEN_REFRESH"

    # Attack detections
    SQL_INJECTION    = "SQL_INJECTION"
    XSS_ATTEMPT      = "XSS_ATTEMPT"
    CMD_INJECTION    = "CMD_INJECTION"
    RATE_LIMIT_HIT   = "RATE_LIMIT_HIT"
    IP_BLOCKED       = "IP_BLOCKED"

    # Search events
    SEARCH_BLOCKED   = "SEARCH_BLOCKED"      # content filter blocked result
    SEARCH_PERFORMED = "SEARCH_PERFORMED"

    # System events
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    HISTORY_CLEARED  = "HISTORY_CLEARED"
    SUSPICIOUS_INPUT = "SUSPICIOUS_INPUT"


SEVERITY_MAP = {
    EventType.LOGIN_SUCCESS    : "INFO",
    EventType.SIGNUP_SUCCESS   : "INFO",
    EventType.SEARCH_PERFORMED : "INFO",
    EventType.SETTINGS_CHANGED : "INFO",
    EventType.HISTORY_CLEARED  : "INFO",
    EventType.TOKEN_REFRESH    : "INFO",
    EventType.LOGOUT           : "INFO",
    EventType.SEARCH_BLOCKED   : "WARNING",
    EventType.LOGIN_FAILED     : "WARNING",
    EventType.RATE_LIMIT_HIT   : "WARNING",
    EventType.SUSPICIOUS_INPUT : "WARNING",
    EventType.SQL_INJECTION    : "CRITICAL",
    EventType.XSS_ATTEMPT      : "CRITICAL",
    EventType.CMD_INJECTION    : "CRITICAL",
    EventType.IP_BLOCKED       : "CRITICAL",
}


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def log_security_event(
    db: Session,
    event_type: EventType,
    request: Request,
    user_id: Optional[int] = None,
    details: str = "",
) -> None:
    """
    Write a security event to both:
    1. The database (SecurityEvent table) — for dashboard/reports
    2. The Python logger — for server logs / SIEM integration

    Parameters:
        db         : SQLAlchemy session
        event_type : EventType enum value
        request    : FastAPI request object (to extract IP, path, method)
        user_id    : Optional user ID (None for anonymous)
        details    : Human-readable description of the event
    """
    ip        = _get_client_ip(request)
    severity  = SEVERITY_MAP.get(event_type, "INFO")
    path      = str(request.url.path)
    method    = request.method
    user_agent = request.headers.get("User-Agent", "")[:256]

    # ── Write to DB ───────────────────────────────────────────
    try:
        event = SecurityEvent(
            event_type  = event_type.value,
            severity    = severity,
            ip_address  = ip,
            user_id     = user_id,
            path        = path,
            method      = method,
            user_agent  = user_agent,
            details     = details[:1024],
            created_at  = datetime.utcnow(),
        )
        db.add(event)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write security event to DB: {e}")
        db.rollback()

    # ── Write to Python logger ────────────────────────────────
    log_message = (
        f"[SECURITY] [{severity}] [{event_type.value}] "
        f"IP={ip} | User={user_id or 'anon'} | "
        f"{method} {path} | {details}"
    )

    if severity == "CRITICAL":
        logger.critical(log_message)
    elif severity == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)
