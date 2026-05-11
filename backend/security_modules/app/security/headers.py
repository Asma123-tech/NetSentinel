# app/security/headers.py
# ============================================================
# MODULE 5 — SECURITY HEADERS MIDDLEWARE
# Protects against: Clickjacking, XSS, MIME Sniffing,
#                   Protocol Downgrade (MITM), CSS Injection
# ============================================================

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security-hardening HTTP response headers to every response.

    Headers added:
    ┌─────────────────────────────────────┬─────────────────────────────────────────────────────────┐
    │ Header                              │ What it prevents                                        │
    ├─────────────────────────────────────┼─────────────────────────────────────────────────────────┤
    │ Content-Security-Policy             │ XSS, inline script injection, data exfiltration         │
    │ Strict-Transport-Security (HSTS)    │ Protocol downgrade / MITM attacks (forces HTTPS)        │
    │ X-Frame-Options                     │ Clickjacking (embedding site in <iframe>)                │
    │ X-Content-Type-Options              │ MIME-type sniffing attacks                              │
    │ X-XSS-Protection                    │ Browser-side XSS filter (legacy browsers)               │
    │ Referrer-Policy                     │ Leaking referrer URL to third parties                   │
    │ Permissions-Policy                  │ Restricts browser APIs (camera, mic, geolocation)       │
    │ Cache-Control                       │ Sensitive data cached in browser history                │
    └─────────────────────────────────────┴─────────────────────────────────────────────────────────┘
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # ── 1. Content-Security-Policy (CSP) ─────────────────
        # Restricts which sources can load scripts, styles, images, etc.
        # self  = only from your own domain
        # Prevents injected scripts from running even if XSS succeeds.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "   # unsafe-inline needed for Next.js hydration
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "          # allow images from HTTPS sources
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "                    # block Flash / plugins
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none';"               # no iframes allowed (anti-clickjacking)
        )

        # ── 2. HTTP Strict Transport Security (HSTS) ─────────
        # Tells the browser: ALWAYS use HTTPS for this domain.
        # Even if user types http://, browser upgrades to https://.
        # max-age=31536000 = 1 year | includeSubDomains = applies to all subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # ── 3. X-Frame-Options ───────────────────────────────
        # Prevents your site from being embedded in an <iframe>.
        # Protects against Clickjacking attacks (tricking users into clicking
        # on invisible overlaid frames).
        response.headers["X-Frame-Options"] = "DENY"

        # ── 4. X-Content-Type-Options ────────────────────────
        # Stops browsers from guessing (sniffing) the content type.
        # Prevents attackers from uploading files disguised as safe types.
        response.headers["X-Content-Type-Options"] = "nosniff"

        # ── 5. X-XSS-Protection ──────────────────────────────
        # Enables built-in XSS filter in older browsers (Chrome, IE, Safari).
        # mode=block: completely blocks the page instead of sanitizing.
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # ── 6. Referrer-Policy ───────────────────────────────
        # Controls how much referrer info is sent when navigating away.
        # strict-origin-when-cross-origin:
        #   - Full URL for same-origin requests
        #   - Only origin (no path) for cross-origin requests
        #   - Nothing on downgrade (HTTPS→HTTP)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ── 7. Permissions-Policy ────────────────────────────
        # Disables browser features that this app doesn't need.
        # Prevents malicious scripts from accessing camera, mic, location, etc.
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "fullscreen=(self)"
        )

        # ── 8. Cache-Control (for API responses) ─────────────
        # Prevents sensitive API responses from being cached by proxies
        # or stored in browser history.
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"]        = "no-cache"

        # ── 9. Remove server fingerprinting headers ───────────
        # Don't reveal what tech stack you're running.
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        return response
