# app/routers/media.py
from io import BytesIO
from urllib.parse import unquote_plus

import requests
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FilterMode
from ..services.image_moderation import censor_if_needed
from ..utils.settings import get_or_create_global_settings

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/proxy")
def proxy_image(
    url: str = Query(..., description="Original image URL (URL-encoded)"),
    mode: str = Query(
        None,
        description="Filter mode override: strict / moderate / relaxed",
    ),
    db: Session = Depends(get_db),
):
    decoded_url = unquote_plus(url)

    if not decoded_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid image URL")

    try:
        resp = requests.get(
            decoded_url,
            timeout=10,
            headers={"User-Agent": "NetSentinelProxy/1.0"},
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Failed to fetch remote image")

    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Image not found")

    content_type = resp.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="URL does not point to an image")

    original_bytes = resp.content

    # ── Resolve effective filter mode ──────────────────────────
    # 1. Use the ?mode= param if provided and valid
    # 2. Fall back to the GlobalSettings value from DB
    # 3. Default to strict if neither is available
    settings_obj   = get_or_create_global_settings(db)
    db_mode_str    = getattr(settings_obj, "filter_mode", "strict") or "strict"

    raw_mode = (mode or db_mode_str or "strict").lower().strip()

    # Normalise to enum — default to strict on unrecognised values
    try:
        effective_mode = FilterMode(raw_mode)
    except ValueError:
        effective_mode = FilterMode.strict

    # ── Apply blur based on mode ───────────────────────────────
    # relaxed → no blur (return original)
    # moderate → blur applied (threshold 0.8 kept for future ML integration)
    # strict   → blur applied (threshold 0.6)
    if effective_mode == FilterMode.relaxed:
        final_bytes = original_bytes
    else:
        # Both strict and moderate get blurred
        # threshold param is unused by current Pillow implementation
        # but kept so the call is forward-compatible with ML models
        threshold = 0.6 if effective_mode == FilterMode.strict else 0.8
        final_bytes, _ = censor_if_needed(original_bytes, threshold=threshold)

    return StreamingResponse(BytesIO(final_bytes), media_type="image/jpeg")