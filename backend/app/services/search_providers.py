"""
Search provider service — NetSentinel.

Fetches results from the SearxNG instance and normalises them.

Key features vs the original:
  - FETCH_MULTIPLIER: fetches 4× the requested limit from SearxNG so
    filtering.py has enough headroom to remove explicit text results
    while still returning a full page of clean results.
  - page param: passes pageno to SearxNG for true pagination.
  - _safe_categories: strips the 'adult' category in strict/moderate mode.
  - Protocol-relative URLs: fixes //example.com image URLs → https://
  - mode param in preview_url: tells the media proxy which filter level
    to apply so the AI moderation uses the right threshold.
"""

from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlparse, urlunparse

import requests

from ..config import settings
from ..models import FilterMode


# Raw results fetched from SearxNG = limit × FETCH_MULTIPLIER.
# This gives filtering.py room to remove explicit text results
# without leaving the page short of clean results.
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
        """Remove the 'adult' SearxNG category in strict/moderate modes."""
        if filter_mode == FilterMode.relaxed:
            return self.categories
        cats = [
            c.strip()
            for c in self.categories.split(",")
            if c.strip().lower() != "adult"
        ]
        return ",".join(cats) if cats else "general"

    def _normalize_img_url(self, img: str) -> str:
        """Fix protocol-relative (//host/path) and localhost image URLs."""
        if not img:
            return img

        # Fix protocol-relative URLs  //cdn.example.com/img.jpg
        if img.startswith("//"):
            img = "https:" + img

        parsed_img = urlparse(img)
        base       = urlparse(self.base_url)

        # Fix localhost / missing host (SearxNG sometimes proxies images)
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
        # SearxNG safesearch: 0=off, 1=moderate, 2=strict
        safesearch = {
            FilterMode.strict:   2,
            FilterMode.moderate: 1,
            FilterMode.relaxed:  0,
        }.get(filter_mode, 2)

        # Fetch more than needed so filtering has headroom
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

        # Convert the SearxNG format to our internal dict format
        for item in data.get("results", [])[:fetch_limit]:
            title      = item.get("title") or item.get("url") or "Untitled"
            snippet    = item.get("content") or ""
            result_url = item.get("url") or ""

            img: Optional[str] = item.get("img_src") or item.get("thumbnail")
            preview_url: Optional[str] = None

            if img:
                img = self._normalize_img_url(img)
                # Pass the current filter mode so the media proxy applies
                # the correct AI moderation threshold for this image
                encoded     = quote_plus(img)
                mode_str    = filter_mode.value if hasattr(filter_mode, "value") else str(filter_mode)
                preview_url = f"/api/media/proxy?url={encoded}&mode={mode_str}"

            raw_results.append({
                "title":       title,
                "url":         result_url,
                "snippet":     snippet,
                "preview_url": preview_url,
            })

        return raw_results


# ── Singleton ──────────────────────────────────────────────────

_provider_singleton: Optional[BaseProvider] = None


def get_provider() -> BaseProvider:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = SearxNGProvider()
    return _provider_singleton