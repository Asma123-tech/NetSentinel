# app/security/rate_limiter.py
# ============================================================
# MODULE 3 — RATE LIMITING & ANTI-ABUSE PROTECTION
# Protects against: DDoS, Brute Force, Automated Bots
# ============================================================

import time
import logging
from collections import defaultdict, deque
from threading import Lock
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────
RATE_LIMIT_SEARCH    = 20   # max search requests per window
RATE_LIMIT_AUTH      = 5    # max login/signup attempts per window
RATE_LIMIT_WINDOW    = 60   # seconds (1 minute window)
BLOCK_DURATION       = 300  # seconds to block an IP after too many violations (5 min)
MAX_VIOLATIONS       = 3    # violations before hard-block


class InMemoryRateLimiter:
    """
    Sliding-window rate limiter stored in memory.
    Tracks requests per IP and auto-blocks repeat offenders.

    Structure:
        _requests  : { ip -> deque of timestamps }
        _violations: { ip -> violation count }
        _blocked   : { ip -> unblock_timestamp }
    """

    def __init__(self):
        self._requests:   dict[str, deque] = defaultdict(deque)
        self._violations: dict[str, int]   = defaultdict(int)
        self._blocked:    dict[str, float] = {}
        self._lock = Lock()

    # ── Internal helpers ──────────────────────────────────────

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP (supports X-Forwarded-For)."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_blocked(self, ip: str) -> bool:
        """Return True if IP is currently in the hard-block list."""
        if ip in self._blocked:
            if time.time() < self._blocked[ip]:
                return True
            else:
                # Block expired — clean up
                del self._blocked[ip]
                self._violations[ip] = 0
        return False

    def _prune_old_requests(self, ip: str, window: int):
        """Remove timestamps older than the sliding window."""
        cutoff = time.time() - window
        dq = self._requests[ip]
        while dq and dq[0] < cutoff:
            dq.popleft()

    # ── Public API ────────────────────────────────────────────

    def check(self, request: Request, limit: int, window: int = RATE_LIMIT_WINDOW):
        """
        Call this at the start of any protected endpoint.
        Raises HTTP 429 if the IP is rate-limited or blocked.
        """
        ip = self._get_client_ip(request)

        with self._lock:
            # Hard-blocked?
            if self._is_blocked(ip):
                remaining_block = int(self._blocked.get(ip, 0) - time.time())
                logger.warning(f"Blocked IP attempted access: {ip}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Your IP has been temporarily blocked due to abuse. "
                           f"Try again in {remaining_block}s.",
                    headers={"Retry-After": str(remaining_block)},
                )

            # Prune old entries
            self._prune_old_requests(ip, window)

            request_count = len(self._requests[ip])

            if request_count >= limit:
                # Record violation
                self._violations[ip] += 1
                logger.warning(
                    f"Rate limit exceeded by {ip} "
                    f"({request_count} requests in {window}s, "
                    f"violation #{self._violations[ip]})"
                )

                # Hard-block after too many violations
                if self._violations[ip] >= MAX_VIOLATIONS:
                    self._blocked[ip] = time.time() + BLOCK_DURATION
                    logger.error(
                        f"IP hard-blocked: {ip} after {self._violations[ip]} violations"
                    )
                    raise HTTPException(
                        status_code=429,
                        detail=f"Too many requests. IP blocked for {BLOCK_DURATION}s.",
                        headers={"Retry-After": str(BLOCK_DURATION)},
                    )

                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: max {limit} requests per {window}s. "
                           f"Please slow down.",
                    headers={"Retry-After": str(window)},
                )

            # Record this request
            self._requests[ip].append(time.time())

    def get_stats(self, request: Request) -> dict:
        """Return rate-limit stats for the calling IP (useful for debug/admin)."""
        ip = self._get_client_ip(request)
        with self._lock:
            self._prune_old_requests(ip, RATE_LIMIT_WINDOW)
            return {
                "ip": ip,
                "requests_in_window": len(self._requests[ip]),
                "violations": self._violations.get(ip, 0),
                "is_blocked": self._is_blocked(ip),
            }


# ── Singleton instance (imported by routers) ──────────────────
limiter = InMemoryRateLimiter()


# ── Convenience dependency functions ─────────────────────────
def search_rate_limit(request: Request):
    """FastAPI dependency for search endpoint."""
    limiter.check(request, limit=RATE_LIMIT_SEARCH, window=RATE_LIMIT_WINDOW)


def auth_rate_limit(request: Request):
    """FastAPI dependency for auth endpoints (stricter)."""
    limiter.check(request, limit=RATE_LIMIT_AUTH, window=RATE_LIMIT_WINDOW)
