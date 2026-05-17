from io import BytesIO
from urllib.parse import unquote_plus

import requests
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.image_moderation import censor_if_needed

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/proxy")
def proxy_image(
    url: str = Query(...),
    blur: bool = Query(False),   # only blur when explicitly requested
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
        raise HTTPException(status_code=502, detail="Failed to fetch image")

    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Image not found")

    content_type = resp.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="URL is not an image")

    original_bytes = resp.content

    # Only apply blur when the search router explicitly marks this image
    if blur:
        final_bytes, _ = censor_if_needed(original_bytes)
    else:
        final_bytes = original_bytes

    return StreamingResponse(BytesIO(final_bytes), media_type="image/jpeg")
