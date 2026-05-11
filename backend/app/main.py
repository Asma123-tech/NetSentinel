# app/main.py  — UPDATED (all security modules integrated)
# ============================================================
# SECURITY MODULES INTEGRATED:
#   Module 2 — Input Validation    (used in search router)
#   Module 3 — Rate Limiting       (used in search + auth routers)
#   Module 4 — Authentication      (new /api/auth/* endpoints)
#   Module 5 — Security Headers    (SecurityHeadersMiddleware)
#   Module 6 — Audit Logging       (used across all routers)
# ============================================================

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import search, stats, settings as settings_router
from .routers import media, history

# ── New security routers ──────────────────────────────────────
from .routers.auth import router as auth_router                     # Module 4
from .routers.security_logs import router as security_router        # Module 6

# ── Security middleware ───────────────────────────────────────
from .security.headers import SecurityHeadersMiddleware             # Module 5

# Create all DB tables (including new User + SecurityEvent)
Base.metadata.create_all(bind=engine)

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(
    title="NetSentinel API",
    description="Safe Search Engine with full security hardening",
    version="2.0.0",
)

# ── Middleware stack (order matters — added last, runs first) ──

# Module 5: Security headers on every response
app.add_middleware(SecurityHeadersMiddleware)

# CORS (unchanged — same origins as before)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(search.router,          prefix="/api")   # search (has Module 2 + 3 + 6)
app.include_router(stats.router,           prefix="/api")   # stats (unchanged)
app.include_router(settings_router.router, prefix="/api")   # settings (unchanged)
app.include_router(media.router,           prefix="/api")   # media proxy (unchanged)
app.include_router(history.router,         prefix="/api")   # history (unchanged)
app.include_router(auth_router,            prefix="/api")   # Module 4: auth
app.include_router(security_router,        prefix="/api")   # Module 6: security logs


@app.get("/health")
def health():
    return {"status": "ok", "security": "enabled"}
