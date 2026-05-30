"""
Search provider service — NetSentinel.

Key behaviour:
  - FETCH_MULTIPLIER: fetches 4× limit so filtering has headroom
  - page param: real SearxNG pagination
  - _safe_categories: strips 'adult' in strict/moderate
  - Protocol-relative URL fix: //host → https://host
  - preview_url does NOT embed mode — the frontend's getImageSrc()
    appends &mode=<filterMode> dynamically, so the media proxy always
    receives the correct current mode without duplication.
"""

from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlparse, urlunparse

import requests

from ..config import settings
from ..models import FilterMode

FETCH_MULTIPLIER = 4


class BaseProvider:
    def search(
        self,
        query: str,
        filter_mode: FilterMode,
        limit: int = 10,
        page: int = 1,
    ) -> List[Dict]:
        raise NotImplementedError


class SearxNGProvider(BaseProvider):

    def __init__(
        self,
        base_url: Optional[str] = None,
        categories: Optional[str] = None,
    ):
        self.base_url   = (base_url or settings.SEARXNG_URL).rstrip("/")
        self.categories = categories or settings.SEARXNG_CATEGORIES

    def _safe_categories(self, filter_mode: FilterMode) -> str:
        if filter_mode == FilterMode.relaxed:
            return self.categories
        cats = [
            c.strip()
            for c in self.categories.split(",")
            if c.strip().lower() != "adult"
        ]
        return ",".join(cats) if cats else "general"

    def _normalize_img_url(self, img: str) -> str:
        if not img:
            return img
        # Fix protocol-relative URLs: //cdn.example.com → https://cdn.example.com
        if img.startswith("//"):
            img = "https:" + img
        parsed_img = urlparse(img)
        base       = urlparse(self.base_url)
        if parsed_img.hostname in ("localhost", "127.0.0.1") or not parsed_img.netloc:
            parsed_img = parsed_img._replace(
                scheme=base.scheme, netloc=base.netloc
            )
            img = urlunparse(parsed_img)
        return img

    def search(
        self,
        query: str,
        filter_mode: FilterMode,
        limit: int = 10,
        page: int = 1,
    ) -> List[Dict]:
        safesearch = {
            FilterMode.strict:   2,
            FilterMode.moderate: 1,
            FilterMode.relaxed:  0,
        }.get(filter_mode, 2)

        fetch_limit = limit * FETCH_MULTIPLIER

        params = {
            "q":          query,
            "format":     "json",
            "categories": self._safe_categories(filter_mode),
            "language":   "en",
            "safesearch": safesearch,
            "pageno":     page,
        }

        resp = requests.get(
            f"{self.base_url}/search",
            params=params,
            headers={"User-Agent": "NetSentinelSafeSearch/1.0 (student project)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_results: List[Dict] = []

        for item in data.get("results", [])[:fetch_limit]:
            title      = item.get("title") or item.get("url") or "Untitled"
            snippet    = item.get("content") or ""
            result_url = item.get("url") or ""

            img: Optional[str] = item.get("img_src") or item.get("thumbnail")
            preview_url: Optional[str] = None

            if img:
                img = self._normalize_img_url(img)
                encoded = quote_plus(img)
                # Do NOT embed mode here — frontend getImageSrc() appends
                # &mode=<currentMode> dynamically to avoid duplication
                preview_url = f"/api/media/proxy?url={encoded}"

            raw_results.append({
                "title":       title,
                "url":         result_url,
                "snippet":     snippet,
                "preview_url": preview_url,
            })

        return raw_results


_provider_singleton: Optional[BaseProvider] = None


def get_provider() -> BaseProvider:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = SearxNGProvider()
    return _provider_singleton