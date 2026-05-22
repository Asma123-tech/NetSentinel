"""
Content filtering service for NetSentinel.

FIXES vs original:
  1. Uses regex word-boundary matching (\b) instead of plain substring
     matching — prevents false positives like "essex" matching "sex".
  2. Checks the result URL / domain as well as title + snippet.
  3. STRICT_KEYWORDS expanded to ~50 explicit terms.
  4. Added a hardcoded BLOCKED_DOMAINS set for high-traffic adult sites
     that should always be blocked regardless of their page titles.
  5. MODERATE_KEYWORDS expanded to cover more common explicit terms.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from ..models import FilterMode, ResultType


# ── Keyword lists ──────────────────────────────────────────────
# All lowercase. Matched with \b word boundaries so "sex" does NOT
# match "essex", "middlesex", "sexuality" in legitimate educational
# contexts (though "sexual" itself is still in the list for strict mode).

STRICT_KEYWORDS: Set[str] = {
    # Core explicit terms
    "porn", "pornography", "porno", "pornographic",
    "xxx", "x-rated", "xrated",
    "nude", "nudity", "nudist", "naked",
    "nsfw", "adult content", "adult site",
    "sex tape", "sex video", "sex scene",
    "erotic", "erotica", "eroticism",
    "hentai", "ecchi", "doujin",
    "explicit", "explicit content",
    "obscene", "obscenity",

    # Acts / body (clinical terms acceptable in education — blocked here for safety)
    "masturbation", "masturbate",
    "orgasm", "ejaculation",
    "intercourse", "fornication",
    "genitals", "genital",
    "penis", "vagina", "vulva", "anus", "rectum",
    "breasts", "nipple", "nipples",
    "pubic",

    # Industry / fetish terms
    "fetish", "bondage", "bdsm", "dominatrix", "sadomasochism",
    "escort service", "call girl", "sex worker", "prostitute", "prostitution",
    "brothel", "bordello", "red light",
    "cam girl", "camgirl", "onlyfans", "only fans",
    "stripper", "strip club", "lap dance",
    "playboy", "penthouse",

    # Violent / illegal sexual content
    "rape", "molestation", "child porn", "child abuse",
    "incest", "bestiality",

    # Common euphemisms used in explicit content titles
    "milf", "gilf", "dilf",
    "threesome", "gangbang", "orgy",
    "creampie", "cumshot", "blowjob", "handjob",
    "amateur sex", "homemade sex",
}

MODERATE_KEYWORDS: Set[str] = {
    # A smaller set — filters the most obvious terms but allows more through
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

# Relaxed mode applies zero base keyword blocking.
# Custom blocked_keywords from settings still apply.
RELAXED_KEYWORDS: Set[str] = set()


# ── Domain blocklist ───────────────────────────────────────────
# High-traffic explicit sites blocked at domain level in strict/moderate modes.
# These are blocked even if their page titles look clean.

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
    "redlight.de", "sexfilme.de",
}

# Moderate mode uses a smaller domain blocklist
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
    """
    Compile a single regex that matches any keyword at a word boundary.
    Using one compiled pattern is much faster than looping over keywords.
    Multi-word phrases use a simple space/non-word boundary approach.
    """
    if not keywords:
        return None

    parts = []
    for kw in keywords:
        if " " in kw:
            # Multi-word phrase: match with \b at start and end
            escaped = re.escape(kw)
            parts.append(rf"\b{escaped}\b")
        else:
            parts.append(rf"\b{re.escape(kw)}\b")

    pattern = "|".join(parts)
    return re.compile(pattern, re.IGNORECASE)


def text_contains_banned(text: str, pattern: Optional[re.Pattern]) -> bool:
    """Returns True if the text matches any banned keyword (word-boundary aware)."""
    if pattern is None:
        return False
    return bool(pattern.search(text))


def parse_csv(text: str) -> List[str]:
    if not text:
        return []
    return [x.strip().lower() for x in text.split(",") if x.strip()]


def get_root_domain(url: str) -> str:
    """Extract root domain (e.g. 'pornhub.com') from a full URL."""
    try:
        hostname = urlparse(url).hostname or ""
        # Strip leading 'www.' or other subdomains — compare root domain only
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

    Blocking logic (in order):
      1. Domain blocklist (hardcoded explicit sites)
      2. Allowed domains whitelist (if configured — blocks everything else)
      3. Keyword scan on title + snippet + URL path
    """
    base_keywords   = get_base_keywords(filter_mode)
    extra_blocked   = set(parse_csv(blocked_keywords))
    all_keywords    = base_keywords.union(extra_blocked)
    blocked_domains = get_blocked_domains(filter_mode)

    allowed_set = set(parse_csv(allowed_domains))

    # Compile one pattern for the full keyword set (fast single-pass matching)
    pattern = _build_pattern(all_keywords)

    filtered: List[Dict] = []
    blocked_count = 0

    for r in raw_results:
        url        = r.get("url", "")
        title      = r.get("title", "")
        snippet    = r.get("snippet", "") or ""
        root_dom   = get_root_domain(url)
        full_dom   = (urlparse(url).hostname or "").lower()

        # ── 1. Hardcoded domain blocklist ─────────────────────
        if root_dom in blocked_domains or full_dom in blocked_domains:
            blocked_count += 1
            continue

        # ── 2. Allowed-domains whitelist ──────────────────────
        # If any allowed domains are configured, block everything outside that list
        if allowed_set and root_dom not in allowed_set and full_dom not in allowed_set:
            blocked_count += 1
            continue

        # ── 3. Keyword scan ───────────────────────────────────
        scan_text = f"{title} {snippet} {url}"
        is_explicit = text_contains_banned(scan_text, pattern)

        if is_explicit:
            has_image = bool(r.get("preview_url"))
            if has_image:
                # Show image results but mark them for blurring
                r_copy = r.copy()
                r_copy["blur_image"] = True
                filtered.append(r_copy)
            else:
                # Block explicit text/link results entirely
                blocked_count += 1
            continue

        filtered.append(r)
        return filtered, blocked_count


# ── Result type classification ─────────────────────────────────

def classify_result_type(url: str) -> ResultType:
    u = url.lower()
    if "youtube.com" in u or "vimeo.com" in u or "dailymotion.com" in u:
        return ResultType.video
    if any(u.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return ResultType.image
    return ResultType.text
