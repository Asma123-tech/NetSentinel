# app/utils/settings.py
from sqlalchemy.orm import Session
from .. import models


def get_or_create_global_settings(db: Session) -> models.GlobalSettings:
    """
    Fetch the single GlobalSettings row, creating it with safe defaults if
    it doesn't exist yet.

    Always ensures filter_mode defaults to 'strict' — never 'relaxed'.
    """
    existing = db.query(models.GlobalSettings).first()
    if existing:
        # Guard: if somehow filter_mode ended up empty/null, reset to strict
        if not existing.filter_mode:
            existing.filter_mode = "strict"
            db.add(existing)
            db.commit()
            db.refresh(existing)
        return existing

    # First run — create with strict defaults
    row = models.GlobalSettings(
        filter_mode       = "strict",     # ← explicit default, never relaxed
        parental_controls = True,
        notifications     = True,
        save_history      = True,
        blocked_keywords  = "",
        allowed_domains   = "",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row