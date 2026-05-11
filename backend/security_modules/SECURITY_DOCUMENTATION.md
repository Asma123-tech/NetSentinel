# 🔐 NetSentinel — Security Modules Documentation
### Final Year Project | Cybersecurity Group Contribution

---

## 📁 Files Added / Modified

```
backend/app/
│
├── security/                        ← NEW FOLDER (your cybersecurity contribution)
│   ├── __init__.py
│   ├── input_validator.py           ← Module 2
│   ├── rate_limiter.py              ← Module 3
│   ├── auth.py                      ← Module 4
│   ├── headers.py                   ← Module 5
│   └── audit_logger.py             ← Module 6
│
├── routers/
│   ├── auth.py                      ← NEW (Module 4 endpoints)
│   ├── security_logs.py             ← NEW (Module 6 endpoints)
│   └── search.py                    ← MODIFIED (Modules 2, 3, 6 added)
│
├── models.py                        ← MODIFIED (User + SecurityEvent tables)
├── main.py                          ← MODIFIED (all modules registered)
└── requirements.txt                 ← MODIFIED (new dependencies added)
```

---

## MODULE 2 — Input Validation & Sanitization
**File:** `app/security/input_validator.py`
**Integrated in:** `app/routers/search.py`

### What it does
Every search query submitted by a user is passed through a multi-layer
validation pipeline before it ever reaches the database or search engine.

### How it works
1. **Sanitize** — HTML-encodes dangerous characters (`<`, `>`, `&`, `"`), trims whitespace, enforces 512-char max length
2. **SQL Injection Detection** — 12 regex patterns detect UNION SELECT, DROP TABLE, OR 1=1, SLEEP(), etc.
3. **XSS Detection** — 13 patterns detect `<script>`, `javascript:`, `onerror=`, `eval()`, etc.
4. **Command Injection Detection** — Detects pipe chaining (`| ls`), backtick execution, `$()` substitution

### Attack Example Blocked
```
User types: " OR 1=1; DROP TABLE users; --
System:     ✗ BLOCKED | Logged as SQL_INJECTION | HTTP 400 returned
```

### API Behavior
- Clean query → proceeds normally
- Malicious query → HTTP 400 + attack logged in DB

---

## MODULE 3 — Rate Limiting & Anti-Abuse Protection
**File:** `app/security/rate_limiter.py`
**Integrated in:** `app/routers/search.py` and `app/routers/auth.py`

### What it does
Prevents automated bots, DDoS attacks, and brute-force attempts by limiting
how many requests a single IP address can make per time window.

### How it works
- **Sliding window algorithm** — tracks timestamps of recent requests per IP
- **Two limits:**
  - Search: max 20 requests/minute per IP
  - Login/Signup: max 5 requests/minute per IP (stricter)
- **Violation tracking** — after 3 violations, IP is hard-blocked for 5 minutes
- **X-Forwarded-For support** — works correctly behind reverse proxies

### Example Scenario
```
IP: 192.168.1.50 makes 21 search requests in 60 seconds
→ Request 21: HTTP 429 "Rate limit exceeded"
→ After 3 such violations: IP blocked for 300 seconds
→ Logged as RATE_LIMIT_HIT + IP_BLOCKED
```

---

## MODULE 4 — Secure Authentication & Session Management
**Files:** `app/security/auth.py`, `app/routers/auth.py`
**New DB table:** `users`

### What it does
Provides secure user registration and login using JWT tokens and bcrypt
password hashing. Protects against session hijacking and account takeover.

### How it works
- **bcrypt hashing** — passwords stored as salted bcrypt hashes (never plaintext)
- **Password policy** — enforces 8+ chars, uppercase, lowercase, digit, special character
- **JWT Access Tokens** — short-lived (30 min), signed with HS256
- **JWT Refresh Tokens** — longer-lived (7 days), used to get new access tokens
- **Timing-safe login** — always runs bcrypt.verify() even for non-existent users (prevents username enumeration)
- **Token type enforcement** — access tokens can't be used as refresh tokens and vice versa

### API Endpoints Added
| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| POST   | /api/auth/signup      | Register new user                    |
| POST   | /api/auth/login       | Login, returns access + refresh JWT  |
| POST   | /api/auth/refresh     | Exchange refresh token for new access|
| GET    | /api/auth/me          | Get current user profile             |

### How to protect any route
```python
from app.security.auth import get_current_active_user

@router.get("/protected-endpoint")
def my_protected_route(user = Depends(get_current_active_user)):
    return {"message": f"Hello {user.username}"}
```

---

## MODULE 5 — Security Headers Middleware
**File:** `app/security/headers.py`
**Integrated in:** `app/main.py`

### What it does
Automatically adds security HTTP headers to every single API response.
These headers instruct the browser to apply additional protections.

### Headers Added & What They Prevent

| Header | Value | Prevents |
|--------|-------|----------|
| Content-Security-Policy | default-src 'self'; object-src 'none' | XSS, script injection, data exfiltration |
| Strict-Transport-Security | max-age=31536000; includeSubDomains | MITM attacks, protocol downgrade |
| X-Frame-Options | DENY | Clickjacking attacks |
| X-Content-Type-Options | nosniff | MIME-type sniffing attacks |
| X-XSS-Protection | 1; mode=block | Browser-side XSS filter |
| Referrer-Policy | strict-origin-when-cross-origin | URL leakage to third parties |
| Permissions-Policy | camera=(), microphone=() | Prevents accessing device APIs |
| Cache-Control (API routes) | no-store, private | Sensitive data in browser cache |

### Additional Hardening
- Removes `Server` header (hides backend tech stack)
- Removes `X-Powered-By` header (hides framework info)

---

## MODULE 6 — Audit Logging & Intrusion Detection
**Files:** `app/security/audit_logger.py`, `app/routers/security_logs.py`
**New DB table:** `security_events`

### What it does
Records every security-relevant event to the database. Provides an admin
API to view logs, detect intrusions, and generate security reports.

### Event Types Tracked
| Event Type | Severity | Description |
|------------|----------|-------------|
| SQL_INJECTION | CRITICAL | SQL injection attempt detected |
| XSS_ATTEMPT | CRITICAL | XSS script injection detected |
| CMD_INJECTION | CRITICAL | Command injection detected |
| IP_BLOCKED | CRITICAL | IP hard-blocked after violations |
| LOGIN_FAILED | WARNING | Failed login attempt |
| RATE_LIMIT_HIT | WARNING | IP exceeded rate limit |
| SUSPICIOUS_INPUT | WARNING | Unusual input patterns |
| LOGIN_SUCCESS | INFO | Successful login |
| SEARCH_PERFORMED | INFO | Normal search query |
| SETTINGS_CHANGED | INFO | Settings updated |

### API Endpoints Added
| Method | Endpoint                    | Description                         |
|--------|-----------------------------|-------------------------------------|
| GET    | /api/security/logs          | Get all security events (filterable)|
| GET    | /api/security/summary       | Aggregated attack statistics        |
| GET    | /api/security/threats       | CRITICAL events only                |

### Log Format (Server Logs)
```
2026-03-04 21:30:15 | CRITICAL  | security | [SECURITY] [CRITICAL] [SQL_INJECTION]
                                              IP=192.168.1.50 | User=anon | POST /api/search
                                              | Blocked query: "' OR 1=1--"
```

---

## 🔧 Setup Instructions

### 1. Install new dependencies
```bash
pip install python-jose[cryptography] passlib[bcrypt] email-validator
```
Or update requirements.txt and run:
```bash
pip install -r requirements.txt
```

### 2. Set environment variable for JWT secret
In your `.env` file:
```env
JWT_SECRET_KEY=your-very-long-random-secret-key-here-minimum-32-chars
```
Generate a secure key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Copy files into your project
Copy everything from the `security/` folder into `backend/app/security/`
Copy updated `main.py`, `models.py`, `routers/search.py` to their locations.

### 4. Restart the backend
```bash
docker-compose down && docker-compose up --build
```
New DB tables (`users`, `security_events`) will be created automatically.

---

## ✅ Security Testing Checklist

Test each module is working:

**Module 2 (Input Validation)**
- [ ] Send query `' OR 1=1--` → should return HTTP 400
- [ ] Send query `<script>alert(1)</script>` → should return HTTP 400
- [ ] Send normal query → should work fine

**Module 3 (Rate Limiting)**
- [ ] Send 21 search requests in 1 minute → 21st should return HTTP 429
- [ ] Send 6 login attempts in 1 minute → 6th should return HTTP 429

**Module 4 (Authentication)**
- [ ] POST /api/auth/signup with valid data → returns JWT tokens
- [ ] POST /api/auth/login with correct credentials → returns JWT tokens
- [ ] POST /api/auth/login with wrong password → returns HTTP 401
- [ ] GET /api/auth/me with valid token → returns user profile
- [ ] GET /api/auth/me without token → returns HTTP 401

**Module 5 (Security Headers)**
- [ ] Open browser DevTools → Network → any API call
- [ ] Check Response Headers for: CSP, HSTS, X-Frame-Options, etc.

**Module 6 (Audit Logging)**
- [ ] GET /api/security/logs → shows event list
- [ ] GET /api/security/summary → shows attack counts
- [ ] Trigger a SQLi attempt → check it appears in /api/security/threats
