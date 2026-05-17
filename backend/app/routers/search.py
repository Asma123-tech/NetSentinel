# app/routers/search.py  — UPDATED (Modules 2, 3, 6 integrated)
# ============================================================
# Changes from original:
#   + Module 2: validate_search_query() called before searching
#   + Module 3: search_rate_limit dependency
#   + Module 6: log_security_event() for attacks + searches
# ============================================================

import logging
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import requests

from .. import models, schemas
from ..database import get_db
from ..services.search_providers import get_provider
from ..services.filtering import filter_results, classify_result_type
from ..utils.settings import get_or_create_global_settings
from ..models import ResultType

# ── Security imports ──────────────────────────────────────────
from ..security.input_validator import validate_search_query, sanitize_input  # Module 2
from ..security.rate_limiter import search_rate_limit                          # Module 3
from ..security.audit_logger import log_security_event, EventType             # Module 6

router = APIRouter(prefix="/search", tags=["search"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def infer_result_type(r: Dict) -> ResultType:
    if r.get("preview_url"):
        return ResultType.image
    return classify_result_type(r["url"])


@router.post("", response_model=schemas.SearchResponse)
def perform_search(
    payload: schemas.SearchRequest,
    request: Request,                           # needed for logging + rate limiting
    db: Session = Depends(get_db),
    _rl=Depends(search_rate_limit),             # Module 3: rate limit check
):
    # ── Module 2: Sanitize input ──────────────────────────────
    sanitized_query = sanitize_input(payload.query)

    # ── Module 2: Validate for SQLi / XSS / CMDi ─────────────
    is_safe, reason = validate_search_query(sanitized_query)
    if not is_safe:
        # Module 6: Log the attack attempt
        log_security_event(
            db,
            EventType.SQL_INJECTION if "SQL" in reason else EventType.XSS_ATTEMPT,
            request,
            details=f"Blocked query: {payload.query[:200]!r} | Reason: {reason}",
        )
        raise HTTPException(status_code=400, detail=reason)

    if not sanitized_query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    provider = get_provider()
    settings = get_or_create_global_settings(db)
    effective_mode = payload.filter_mode or settings.filter_mode

    try:
        raw_results = provider.search(sanitized_query, filter_mode=effective_mode, limit=payload.limit)
        has_more = len(raw_results) == payload.limit
    except requests.HTTPError:
        logger.exception("Upstream search provider HTTP error")
        return schemas.SearchResponse(results=[], has_more=False)
    except requests.RequestException:
        logger.exception("Failed to contact upstream search provider")
        return schemas.SearchResponse(results=[], has_more=False)
    except Exception:
        raise

    filtered, blocked_count = filter_results(
        raw_results,
        filter_mode=effective_mode,
        blocked_keywords=settings.blocked_keywords or "",
        allowed_domains=settings.allowed_domains or "",
    )

    total = len(raw_results)
    safe  = len(filtered)

    # Module 6: Log the search (non-attack)
    log_security_event(
        db,
        EventType.SEARCH_PERFORMED,
        request,
        details=f"Query={sanitized_query[:100]!r} | Safe={safe} | Blocked={blocked_count}",
    )

    # ── CASE 1: Don't save history ─────────────────────────────
    if not settings.save_search_history:
        now = datetime.utcnow()
        out: List[schemas.SearchResultOut] = []
        for idx, r in enumerate(filtered, start=1):
            if not r.get("url"):
                continue
            out.append(
                schemas.SearchResultOut(
                    id=idx,
                    title=r["title"],
                    url=r["url"],
                    snippet=r["snippet"],
                    type=infer_result_type(r).value,
                    timestamp=now,
                    preview_url=r.get("preview_url"),
                )
            )
        return schemas.SearchResponse(results=out, has_more=has_more)

    # ── CASE 2: Save query + results ──────────────────────────
    q = models.SearchQuery(
        query=sanitized_query,          # store sanitized version
        filter_mode=effective_mode,
        total_results=total,
        safe_results=safe,
        blocked_results=blocked_count,
    )
    db.add(q)
    db.flush()

    db_results: List[models.SearchResult] = []
    for r in filtered:
        if not r.get("url"):
            continue
        row = models.SearchResult(
            query_id=q.id,
            title=r["title"],
            url=r["url"],
            snippet=r["snippet"],
            type=infer_result_type(r).value,
            is_blocked=False,
        )
        db.add(row)
        db_results.append(row)

    db.commit()
    db.refresh(q)

    out: List[schemas.SearchResultOut] = []
    for r, row in zip(filtered, db_results):
        out.append(
            schemas.SearchResultOut(
                id=row.id,
                title=row.title,
                url=row.url,
                snippet=row.snippet,
                type=row.type,
                timestamp=row.created_at,
                preview_url=r.get("preview_url"),
            )
        )
    return schemas.SearchResponse(results=out, has_more=has_more)
