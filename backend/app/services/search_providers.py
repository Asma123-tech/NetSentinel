"""
Search provider service for NetSentinel.

FIXES vs original:
  1. Fetches a buffer of results (limit × FETCH_MULTIPLIER) from SearxNG
     so that after filtering.py removes explicit content, enough clean
     results remain. Previously, fetching exactly `limit` results meant
     filtering could leave only 5-8 visible results on mobile.
  2. Excludes the SearxNG "adult" category in strict/moderate modes so
     the source itself is cleaner before filtering runs.
  3. No other logic changes — safesearch mapping, URL normalisation,
     and provider singleton are unchanged.
"""

from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlparse, urlunparse

import requests

from ..config import settings
from ..models import FilterMode


# How many raw results to fetch from SearxNG per `limit` requested.
# e.g. if the frontend wants 20 results and the multiplier is 4,
# we fetch 80 from SearxNG — filtering then reduces it to ≤20 clean ones.
FETCH_MULTIPLIER = 4


class BaseProvider:
    def search(
        self,
        query: str,
        filter_mode: FilterMode,
        limit: int = 10,
    ) -> List[Dict]:
        raise NotImplementedError


class SearxNGProvider(BaseProvider):
    """
    Calls your SearxNG instance /search?format=json and normalises results
    to {title, url, snippet, preview_url}.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        categories: Optional[str] = None,
    ):
        self.base_url   = (base_url or settings.SEARXNG_URL).rstrip("/")
        self.categories = categories or settings.SEARXNG_CATEGORIES

    def _safe_categories(self, filter_mode: FilterMode) -> str:
        """
        Remove the 'adult' category from the SearxNG request in strict/moderate
        modes so SearxNG itself doesn't route the query to adult engines.
        In relaxed mode the configured categories are used as-is.
        """
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

        parsed_img = urlparse(img)
        base = urlparse(self.base_url)  # e.g. http://searxng:8080

        # If SearxNG returned a localhost/relative URL, swap in the container host
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
    ) -> List[Dict]:
        # SearxNG safesearch: 0=off, 1=moderate, 2=strict
        safesearch_map = {
            FilterMode.strict:   2,
            FilterMode.moderate: 1,
            FilterMode.relaxed:  0,
        }
        safesearch = safesearch_map.get(filter_mode, 2)

        # Fetch a multiple of the requested limit so filtering has headroom
        fetch_limit = limit * FETCH_MULTIPLIER

        params = {
            "q":          query,
            "format":     "json",
            "categories": self._safe_categories(filter_mode),
            "language":   "en",
            "safesearch": safesearch,
            "pageno":     1,
        }

        url     = f"{self.base_url}/search"
        headers = {
            "User-Agent": (
                "NetSentinelSafeSearch/1.0 "
                "(student project; contact: youremail@example.com)"
            )
        }

        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        raw_results: List[Dict] = []

        # Slice at fetch_limit (not limit) — filtering.py will reduce further
        for item in data.get("results", [])[:fetch_limit]:
            title      = item.get("title") or item.get("url") or "Untitled"
            snippet    = item.get("content") or ""
            result_url = item.get("url") or ""

            img: Optional[str] = item.get("img_src") or item.get("thumbnail")
            preview_url: Optional[str] = None

            if img:
                img = self._normalize_img_url(img)
                encoded     = quote_plus(img)
                preview_url = f"/api/media/proxy?url={encoded}"

            raw_results.append(
                {
                    "title":       title,
                    "url":         result_url,
                    "snippet":     snippet,
                    "preview_url": preview_url,
                }
            )

        return raw_results


# ── Singleton ──────────────────────────────────────────────────

_provider_singleton: BaseProvider | None = None


def get_provider() -> BaseProvider:
    global _provider_singleton
    if _provider_singleton is not None:
        return _provider_singleton

    if settings.SEARCH_PROVIDER.lower() == "searxng":
        _provider_singleton = SearxNGProvider()
    else:
        _provider_singleton = SearxNGProvider()

    return _provider_singleton