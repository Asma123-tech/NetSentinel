# app/routers/security_logs.py
# ============================================================
# MODULE 6 — SECURITY LOGS ROUTER
# Endpoints to view audit logs & intrusion detection reports
# ============================================================

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SecurityEvent

router = APIRouter(prefix="/security", tags=["security"])


# ── Pydantic output schemas ───────────────────────────────────

class SecurityEventOut(BaseModel):
    id: int
    event_type: str
    severity: str
    ip_address: str
    user_id: Optional[int]
    path: str
    method: str
    details: str
    created_at: datetime

    class Config:
        orm_mode = True


class SecuritySummary(BaseModel):
    total_events: int
    critical_events: int
    warning_events: int
    sql_injection_attempts: int
    xss_attempts: int
    rate_limit_hits: int
    ip_blocks: int
    failed_logins: int
    last_event_at: Optional[datetime]


# ── GET /api/security/logs ────────────────────────────────────

@router.get("/logs", response_model=List[SecurityEventOut])
def get_security_logs(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
    severity: Optional[str] = Query(None, description="Filter by: INFO | WARNING | CRITICAL"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
):
    """
    Retrieve security audit logs.
    Used in the admin dashboard to monitor suspicious activity.
    """
    q = db.query(SecurityEvent).order_by(desc(SecurityEvent.created_at))

    if severity:
        q = q.filter(SecurityEvent.severity == severity.upper())

    if event_type:
        q = q.filter(SecurityEvent.event_type == event_type.upper())

    return q.limit(limit).all()


# ── GET /api/security/summary ─────────────────────────────────

@router.get("/summary", response_model=SecuritySummary)
def get_security_summary(db: Session = Depends(get_db)):
    """
    Aggregated security statistics — perfect for the security dashboard.
    Shows a bird's-eye view of all attack attempts and events.
    """
    from sqlalchemy import func

    def count_by_type(event_type_val: str) -> int:
        return db.query(func.count(SecurityEvent.id)).filter(
            SecurityEvent.event_type == event_type_val
        ).scalar() or 0

    def count_by_severity(sev: str) -> int:
        return db.query(func.count(SecurityEvent.id)).filter(
            SecurityEvent.severity == sev
        ).scalar() or 0

    total        = db.query(func.count(SecurityEvent.id)).scalar() or 0
    last_event   = db.query(SecurityEvent).order_by(desc(SecurityEvent.created_at)).first()

    return SecuritySummary(
        total_events           = total,
        critical_events        = count_by_severity("CRITICAL"),
        warning_events         = count_by_severity("WARNING"),
        sql_injection_attempts = count_by_type("SQL_INJECTION"),
        xss_attempts           = count_by_type("XSS_ATTEMPT"),
        rate_limit_hits        = count_by_type("RATE_LIMIT_HIT"),
        ip_blocks              = count_by_type("IP_BLOCKED"),
        failed_logins          = count_by_type("LOGIN_FAILED"),
        last_event_at          = last_event.created_at if last_event else None,
    )


# ── GET /api/security/threats ─────────────────────────────────

@router.get("/threats", response_model=List[SecurityEventOut])
def get_threats_only(db: Session = Depends(get_db), limit: int = 100):
    """
    Return only CRITICAL severity events (actual attack attempts).
    Used for intrusion detection alerts.
    """
    return (
        db.query(SecurityEvent)
        .filter(SecurityEvent.severity == "CRITICAL")
        .order_by(desc(SecurityEvent.created_at))
        .limit(limit)
        .all()
    )
