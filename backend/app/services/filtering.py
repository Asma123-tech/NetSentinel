"""
Content filtering service — NetSentinel.

Filters raw search results using:
  1. Hardcoded domain blocklist   — high-traffic adult sites blocked by domain
  2. Allowed-domains whitelist    — if configured, blocks everything outside
  3. Keyword scan (text results)  — explicit text/link results are removed

NOTE ON IMAGE RESULTS:
  Image results that contain explicit keywords in their title/snippet/URL
  are NOT removed here.  Instead they are passed to the media proxy with
  the current filter mode so the AI moderation pipeline (NudeNet +
  HuggingFace) can decide whether to blur them.  This gives accurate,
  content-aware filtering instead of over-blocking based on words alone
  (e.g. a medical article about "breast cancer" would be wrongly blocked
  by pure keyword matching).
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from ..models import FilterMode


# ── Keyword lists ──────────────────────────────────────────────

STRICT_KEYWORDS: Set[str] = {
    "porn", "pornography", "porno", "pornographic",
    "xxx", "x-rated", "xrated",
    "nude", "nudity", "nudist", "naked",
    "nsfw", "adult content", "adult site",
    "sex tape", "sex video", "sex scene",
    "erotic", "erotica", "eroticism",
    "hentai", "ecchi", "doujin",
    "explicit", "explicit content",
    "obscene", "obscenity",
    "masturbation", "masturbate",
    "orgasm", "ejaculation",
    "intercourse", "fornication",
    "genitals", "genital",
    "penis", "vagina", "vulva", "anus", "rectum",
    "breasts", "nipple", "nipples",
    "pubic",
    "fetish", "bondage", "bdsm", "dominatrix", "sadomasochism",
    "escort service", "call girl", "sex worker", "prostitute", "prostitution",
    "brothel", "bordello", "red light",
    "cam girl", "camgirl", "onlyfans", "only fans",
    "stripper", "strip club", "lap dance",
    "playboy", "penthouse",
    "rape", "molestation", "child porn", "child abuse",
    "incest", "bestiality",
    "milf", "gilf", "dilf",
    "threesome", "gangbang", "orgy",
    "creampie", "cumshot", "blowjob", "handjob",
    "amateur sex", "homemade sex",
}

MODERATE_KEYWORDS: Set[str] = {
    "porn", "pornography", "porno",
    "xxx", "x-rated",
    "nude", "nudity", "naked",
    "nsfw",
    "erotic", "erotica",
    "hentai",
    "explicit content",
    "fetish", "bondage", "bdsm",
    "onlyfans", "only fans",
    "cam girl", "camgirl",
    "prostitute", "prostitution",
    "child porn", "child abuse",
    "rape",
    "milf", "threesome", "gangbang", "orgy",
    "blowjob", "handjob", "cumshot",
}

RELAXED_KEYWORDS: Set[str] = set()


# ── Domain blocklists ──────────────────────────────────────────

BLOCKED_DOMAINS_STRICT: Set[str] = {
    "pornhub.com", "xvideos.com", "xhamster.com", "xnxx.com",
    "redtube.com", "youporn.com", "tube8.com", "spankbang.com",
    "brazzers.com", "bangbros.com", "naughtyamerica.com",
    "realitykings.com", "mofos.com", "twistys.com",
    "onlyfans.com", "fansly.com", "manyvids.com",
    "chaturbate.com", "myfreecams.com", "livejasmin.com",
    "bongacams.com", "stripchat.com", "cam4.com",
    "playboy.com", "penthouse.com", "hustler.com",
    "adultfriendfinder.com", "ashleymadison.com",
    "rule34.xxx", "gelbooru.com", "danbooru.donmai.us",
    "nhentai.net", "e-hentai.org", "hentaihaven.xxx",
    "literotica.com", "sexstories.com",
}

BLOCKED_DOMAINS_MODERATE: Set[str] = {
    "pornhub.com", "xvideos.com", "xhamster.com", "xnxx.com",
    "redtube.com", "youporn.com", "tube8.com", "spankbang.com",
    "onlyfans.com", "fansly.com",
    "chaturbate.com", "myfreecams.com", "livejasmin.com",
    "nhentai.net", "e-hentai.org",
    "adultfriendfinder.com",
}


# ── Helpers ────────────────────────────────────────────────────

def get_base_keywords(mode: FilterMode) -> Set[str]:
    if mode == FilterMode.strict:
        return STRICT_KEYWORDS
    if mode == FilterMode.moderate:
        return MODERATE_KEYWORDS
    return RELAXED_KEYWORDS


def get_blocked_domains(mode: FilterMode) -> Set[str]:
    if mode == FilterMode.strict:
        return BLOCKED_DOMAINS_STRICT
    if mode == FilterMode.moderate:
        return BLOCKED_DOMAINS_MODERATE
    return set()


def _build_pattern(keywords: Set[str]) -> Optional[re.Pattern]:
    """Compile all keywords into one fast regex with word boundaries."""
    if not keywords:
        return None
    parts = [rf"\b{re.escape(kw)}\b" for kw in keywords]
    return re.compile("|".join(parts), re.IGNORECASE)


def text_contains_banned(text: str, pattern: Optional[re.Pattern]) -> bool:
    if pattern is None:
        return False
    return bool(pattern.search(text))


def parse_csv(text: str) -> List[str]:
    if not text:
        return []
    return [x.strip().lower() for x in text.split(",") if x.strip()]


def get_root_domain(url: str) -> str:
    try:
        hostname = urlparse(url).hostname or ""
        parts = hostname.lower().split(".")
        if len(parts) >= 2:
            return f"{parts[-2]}.{parts[-1]}"
        return hostname
    except Exception:
        return ""


# ── Main filter function ───────────────────────────────────────

def filter_results(
    raw_results: List[Dict],
    filter_mode: FilterMode,
    blocked_keywords: str = "",
    allowed_domains: str = "",
) -> Tuple[List[Dict], int]:
    """
    Filter a list of raw search results.

    Returns:
        (filtered_results, blocked_count)

    Blocking order:
      1. Domain blocklist  — always blocks, even for image results
      2. Allowed whitelist — blocks everything outside the whitelist
      3. Keyword scan      — only blocks TEXT results; image results with
                             explicit keywords are allowed through so the
                             AI image moderation pipeline can evaluate them
    """
    base_keywords   = get_base_keywords(filter_mode)
    extra_blocked   = set(parse_csv(blocked_keywords))
    all_keywords    = base_keywords.union(extra_blocked)
    blocked_domains = get_blocked_domains(filter_mode)
    allowed_set     = set(parse_csv(allowed_domains))

    pattern = _build_pattern(all_keywords)

    filtered: List[Dict] = []
    blocked_count = 0

    for r in raw_results:
        url      = r.get("url", "")
        title    = r.get("title", "")
        snippet  = r.get("snippet", "") or ""
        root_dom = get_root_domain(url)
        full_dom = (urlparse(url).hostname or "").lower()

        # ── 1. Domain blocklist ────────────────────────────────
        if root_dom in blocked_domains or full_dom in blocked_domains:
            blocked_count += 1
            continue

        # ── 2. Allowed-domains whitelist ───────────────────────
        if allowed_set and root_dom not in allowed_set and full_dom not in allowed_set:
            blocked_count += 1
            continue

        # ── 3. Keyword scan ────────────────────────────────────
        scan_text   = f"{title} {snippet} {url}"
        is_explicit = text_contains_banned(scan_text, pattern)

        if is_explicit:
            if r.get("preview_url"):
                # Image result with explicit keywords:
                # Let it through — the AI moderation pipeline in media.py
                # will analyse the actual pixel content and blur if needed.
                # This avoids over-blocking safe images whose titles happen
                # to contain ambiguous words.
                filtered.append(r)
            else:
                # Pure text / link result with explicit keywords: block it.
                blocked_count += 1
            continue

        filtered.append(r)

    return filtered, blocked_count


# ── Result type classification ─────────────────────────────────

def classify_result_type(url: str):
    u = url.lower()
    if "youtube.com" in u or "vimeo.com" in u or "dailymotion.com" in u:
        return "video"
    if any(u.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return "image"
    return "text"