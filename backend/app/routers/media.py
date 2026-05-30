"""
Media proxy router — /api/media/proxy

Fetches a remote image through the backend so the frontend never
exposes raw third-party URLs.  In strict / moderate mode every image
is passed through the AI moderation pipeline (NudeNet + HuggingFace).
Only images that the AI detects as explicit get blurred — safe images
are returned untouched.

Query params:
  url   — URL-encoded remote image URL (required)
  mode  — Filter mode: strict | moderate | relaxed  (default: strict)
"""

from io import BytesIO
from urllib.parse import unquote_plus

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.image_moderation import censor_if_needed
from ..utils.settings import get_or_create_global_settings

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/proxy")
def proxy_image(
    url: str = Query(..., description="URL-encoded remote image URL"),
    mode: str = Query(
        None,
        description="Filter mode: strict | moderate | relaxed",
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
    # Priority: ?mode= param → DB global setting → default strict
    settings_obj = get_or_create_global_settings(db)
    db_mode      = getattr(settings_obj, "filter_mode", "strict") or "strict"
    raw_mode     = (mode or db_mode).lower().strip()

    if raw_mode not in ("strict", "moderate", "relaxed"):
        raw_mode = "strict"

    # ── Apply AI moderation ────────────────────────────────────
    # relaxed  → no AI check, return original image
    # moderate → AI check with lenient threshold (0.8)
    # strict   → AI check with tighter threshold (0.6)
    if raw_mode == "relaxed":
        final_bytes = original_bytes
    else:
        threshold   = 0.6 if raw_mode == "strict" else 0.8
        final_bytes, _ = censor_if_needed(original_bytes, threshold=threshold)

    return StreamingResponse(BytesIO(final_bytes), media_type="image/jpeg")