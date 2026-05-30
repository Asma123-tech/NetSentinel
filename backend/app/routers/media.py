"""
Media proxy router — /api/media/proxy

Fetches remote images through the backend so third-party URLs are never
exposed directly to the browser.

In strict / moderate mode every image goes through the AI pipeline.
Additionally, images served from known adult site CDNs are always blurred
regardless of AI result — catching content where the image URL is on a
CDN subdomain that differs from the blocked root domain.

Query params:
  url   — URL-encoded remote image URL (required)
  mode  — strict | moderate | relaxed  (default: strict)
"""

from io import BytesIO
from urllib.parse import unquote_plus, urlparse

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.image_moderation import censor_if_needed
from ..utils.settings import get_or_create_global_settings

router = APIRouter(prefix="/media", tags=["media"])

# ── Adult CDN / domain list ────────────────────────────────────
# These domains serve explicit content images even when the result
# URL appears clean — always blur images from these sources.
_ADULT_DOMAINS = {
    "pornhub.com", "xvideos.com", "xhamster.com", "xnxx.com",
    "redtube.com", "youporn.com", "tube8.com", "spankbang.com",
    "brazzers.com", "bangbros.com", "naughtyamerica.com",
    "onlyfans.com", "fansly.com", "chaturbate.com",
    "myfreecams.com", "livejasmin.com",
    "nhentai.net", "e-hentai.org",
    "tushy.com", "tushy.raw", "tushyraw.com",
    "mofos.com", "realitykings.com", "twistys.com",
    "adultfriendfinder.com",
}


def _root_domain(url: str) -> str:
    try:
        hostname = urlparse(url).hostname or ""
        parts    = hostname.lower().split(".")
        return f"{parts[-2]}.{parts[-1]}" if len(parts) >= 2 else hostname
    except Exception:
        return ""


def _is_adult_cdn(url: str) -> bool:
    """Return True if the image URL originates from a known adult domain."""
    root = _root_domain(url)
    hostname = (urlparse(url).hostname or "").lower()
    return root in _ADULT_DOMAINS or hostname in _ADULT_DOMAINS


@router.get("/proxy")
def proxy_image(
    url: str = Query(..., description="URL-encoded remote image URL"),
    mode: str = Query(None, description="strict | moderate | relaxed"),
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
    settings_obj = get_or_create_global_settings(db)
    db_mode      = getattr(settings_obj, "filter_mode", "strict") or "strict"
    raw_mode     = (mode or db_mode).lower().strip()
    if raw_mode not in ("strict", "moderate", "relaxed"):
        raw_mode = "strict"

    # ── Apply moderation ───────────────────────────────────────
    if raw_mode == "relaxed":
        final_bytes = original_bytes

    else:
        is_strict = (raw_mode == "strict")

        # Always blur images from adult CDNs regardless of AI result
        if _is_adult_cdn(decoded_url):
            from PIL import Image, ImageFilter
            from io import BytesIO as _BytesIO
            try:
                img = Image.open(_BytesIO(original_bytes)).convert("RGB")
                img = img.filter(ImageFilter.GaussianBlur(radius=20))
                out = _BytesIO()
                img.save(out, format="JPEG", quality=85)
                final_bytes = out.getvalue()
            except Exception:
                final_bytes = original_bytes
        else:
            # threshold: strict=0.4 (catches partial exposure), moderate=0.6
            threshold   = 0.4 if is_strict else 0.6
            final_bytes, _ = censor_if_needed(
                original_bytes,
                threshold=threshold,
                strict=is_strict,
            )

    return StreamingResponse(BytesIO(final_bytes), media_type="image/jpeg")