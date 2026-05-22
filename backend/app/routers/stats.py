#app/routera/stats.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=schemas.OverviewStats)
def overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Filter all stats by the logged-in user only
    base = db.query(models.SearchQuery).filter(
        models.SearchQuery.user_id == current_user.id
    )

    total_searches = base.with_entities(
        func.count(models.SearchQuery.id)
    ).scalar() or 0

    blocked_content = base.with_entities(
        func.coalesce(func.sum(models.SearchQuery.blocked_results), 0)
    ).scalar() or 0

    safe_results = base.with_entities(
        func.coalesce(func.sum(models.SearchQuery.safe_results), 0)
    ).scalar() or 0

    active_time_hours = round(total_searches / 60.0, 2)

    return schemas.OverviewStats(
        total_searches    = total_searches,
        blocked_content   = blocked_content,
        safe_results      = safe_results,
        active_time_hours = active_time_hours,
    )


@router.get("/recent", response_model=List[schemas.ActivityItem])
def recent(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 10,
):
    rows = (
        db.query(models.SearchQuery)
        .filter(models.SearchQuery.user_id == current_user.id)
        .order_by(models.SearchQuery.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        schemas.ActivityItem(
            id             = row.id,
            query          = row.query,
            created_at     = row.created_at,
            safe_results   = row.safe_results or 0,
            blocked_results= row.blocked_results or 0,
        )
        for row in rows
    ]
