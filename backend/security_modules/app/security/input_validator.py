# app/security/input_validator.py
# ============================================================
# MODULE 2 — INPUT VALIDATION & SANITIZATION
# Protects against: SQL Injection, XSS, Command Injection
# ============================================================

import re
import html
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ── SQL Injection patterns ────────────────────────────────────
SQL_INJECTION_PATTERNS = [
    r"(\bUNION\b.*\bSELECT\b)",
    r"(\bSELECT\b.*\bFROM\b)",
    r"(\bDROP\b.*\bTABLE\b)",
    r"(\bINSERT\b.*\bINTO\b)",
    r"(\bDELETE\b.*\bFROM\b)",
    r"(\bUPDATE\b.*\bSET\b)",
    r"(--|;|\/\*|\*\/|xp_)",            # SQL comment / stacking
    r"(\bOR\b\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?)",  # OR 1=1
    r"(\bAND\b\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?)", # AND 1=1
    r"(\bEXEC\b|\bEXECUTE\b)",
    r"(\bCAST\b\s*\()",
    r"(\bCONVERT\b\s*\()",
    r"SLEEP\s*\(\d+\)",                  # time-based blind SQLi
    r"BENCHMARK\s*\(",
]

# ── XSS patterns ──────────────────────────────────────────────
XSS_PATTERNS = [
    r"<\s*script[^>]*>",                # <script ...>
    r"javascript\s*:",                   # javascript: protocol
    r"on\w+\s*=\s*['\"]",              # onerror= onclick= etc.
    r"<\s*iframe[^>]*>",
    r"<\s*img[^>]+src\s*=\s*['\"]?\s*javascript",
    r"<\s*object[^>]*>",
    r"<\s*embed[^>]*>",
    r"<\s*link[^>]*>",
    r"vbscript\s*:",
    r"data\s*:text/html",
    r"eval\s*\(",                        # eval() injection
    r"document\.(cookie|write|location)",
    r"window\.(location|open)",
]

# ── Command injection patterns ────────────────────────────────
CMD_INJECTION_PATTERNS = [
    r"[;&|`$]\s*(ls|cat|rm|wget|curl|bash|sh|python|perl|nc|ncat)",
    r"\|\s*\w+",                         # pipe to command
    r"`[^`]+`",                          # backtick command substitution
    r"\$\([^)]+\)",                      # $(command)
]

_SQL_RE  = [re.compile(p, re.IGNORECASE) for p in SQL_INJECTION_PATTERNS]
_XSS_RE  = [re.compile(p, re.IGNORECASE) for p in XSS_PATTERNS]
_CMD_RE  = [re.compile(p, re.IGNORECASE) for p in CMD_INJECTION_PATTERNS]


def sanitize_input(text: str) -> str:
    """
    Sanitize user input:
    1. Strip leading/trailing whitespace
    2. HTML-encode dangerous characters (<, >, &, ", ')
    3. Collapse multiple spaces
    4. Enforce max length (512 chars)
    """
    if not text:
        return ""

    # Trim
    text = text.strip()

    # Max length guard
    if len(text) > 512:
        text = text[:512]
        logger.warning("Input truncated to 512 chars")

    # HTML encode to neutralise <script>, etc.
    text = html.escape(text, quote=True)

    # Collapse repeated whitespace
    text = re.sub(r"\s{2,}", " ", text)

    return text


def detect_sql_injection(text: str) -> Tuple[bool, str]:
    """Returns (is_malicious, matched_pattern)"""
    for pattern in _SQL_RE:
        m = pattern.search(text)
        if m:
            return True, m.group(0)
    return False, ""


def detect_xss(text: str) -> Tuple[bool, str]:
    """Returns (is_malicious, matched_pattern)"""
    for pattern in _XSS_RE:
        m = pattern.search(text)
        if m:
            return True, m.group(0)
    return False, ""


def detect_command_injection(text: str) -> Tuple[bool, str]:
    """Returns (is_malicious, matched_pattern)"""
    for pattern in _CMD_RE:
        m = pattern.search(text)
        if m:
            return True, m.group(0)
    return False, ""


def validate_search_query(query: str) -> Tuple[bool, str]:
    """
    Full validation pipeline for a search query.
    Returns (is_safe, reason).
    
    Usage in router:
        ok, reason = validate_search_query(payload.query)
        if not ok:
            raise HTTPException(status_code=400, detail=reason)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"

    # Check SQL injection
    is_sqli, match = detect_sql_injection(query)
    if is_sqli:
        logger.warning(f"SQL injection attempt blocked: {match!r}")
        return False, "Invalid query: contains disallowed patterns (SQL)"

    # Check XSS
    is_xss, match = detect_xss(query)
    if is_xss:
        logger.warning(f"XSS attempt blocked: {match!r}")
        return False, "Invalid query: contains disallowed patterns (XSS)"

    # Check Command injection
    is_cmd, match = detect_command_injection(query)
    if is_cmd:
        logger.warning(f"Command injection attempt blocked: {match!r}")
        return False, "Invalid query: contains disallowed patterns (CMD)"

    return True, ""
