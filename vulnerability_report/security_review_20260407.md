# Freqy Security Review — 04/07/2026

## Overview

Code security audit of the freqy Flask application (amateur radio frequency coordination database). Reviewed all routes, templates, configuration, database layer, authentication, 2FA, and Docker infrastructure.

## Findings

### Critical / High Priority

#### 1. No CSRF Protection (CRITICAL)
- **Location**: `app/__init__.py` — Flask-WTF `CSRFProtect` not configured
- **Impact**: All state-changing POST endpoints are vulnerable to cross-site request forgery — user deletion, password resets, record edits, NOPC sends, demo resets
- **Affected endpoints**: Every POST handler in `app/routes/admin.py`, `app/routes/records.py`, `app/routes/auth.py`, `app/routes/twofa.py`, `app/routes/profile.py`
- **Fix**: Add `flask-wtf` to requirements, initialize `CSRFProtect(app)` in `app/__init__.py`, add `{{ csrf_token() }}` hidden field to all forms, include `X-CSRFToken` header in all `fetch()` calls

#### 2. No Rate Limiting (CRITICAL)
- **Location**: `app/routes/auth.py` (login, register, forgot-password), `app/routes/twofa.py` (2FA challenge)
- **Impact**: Unlimited login attempts enable credential brute-force; unlimited 2FA attempts enable TOTP brute-force (10^6 combinations); unlimited password reset requests enable email flooding
- **Fix**: Add `flask-limiter` — apply `5/minute` to login, `3/minute` to password reset, `5/minute` to 2FA challenge

#### 3. DOM XSS via innerHTML (HIGH)
- **Location**: `app/templates/profile/edit.html:157,171`
- **Impact**: FCC lookup API response values (`license_class`, `license_status`, field values) inserted into DOM via `innerHTML` without escaping. If FCC data contains HTML/script content, it executes in user's browser.
- **Fix**: Replace `innerHTML` with `textContent`, or escape HTML entities before insertion

#### 4. Missing Security Headers (HIGH)
- **Location**: `app/__init__.py` — no `after_request` handler setting headers
- **Impact**: Vulnerable to clickjacking (no `X-Frame-Options`), MIME sniffing (no `X-Content-Type-Options`), no HSTS enforcement, no Content-Security-Policy
- **Fix**: Add `@app.after_request` handler setting `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, and a baseline CSP

#### 5. Missing Session Cookie Flags (HIGH)
- **Location**: `app/config.py` — `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE` not configured
- **Impact**: Session cookies transmitted over HTTP if accessed without TLS; cookies accessible to JavaScript (XSS escalation); no SameSite protection
- **Fix**: Add `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'` to config

#### 6. Docker Container Runs as Root (HIGH)
- **Location**: `Dockerfile` — no `USER` directive
- **Impact**: Container compromise gives root access inside the container
- **Fix**: Add `RUN useradd -m -u 1000 appuser` and `USER appuser` before `EXPOSE`

### Medium Priority

#### 7. Demo Reset Token Timing Attack
- **Location**: `app/routes/demo.py:19`
- **Code**: `token != cfg_tok` — simple string comparison
- **Fix**: Replace with `hmac.compare_digest(token or '', cfg_tok)`

#### 8. Weak SECRET_KEY Default
- **Location**: `app/config.py:6`
- **Code**: `SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')`
- **Fix**: Fail-fast if SECRET_KEY not set in production, or generate random at runtime

#### 9. 2FA Challenge Not Rate-Limited
- **Location**: `app/routes/twofa.py` — challenge endpoint
- **Impact**: Attacker with stolen password can brute-force 6-digit TOTP without throttling
- **Fix**: Apply rate limit to `/2fa/challenge` endpoint

#### 10. Implicit bcrypt Rounds
- **Location**: `app/auth.py:59`
- **Code**: `bcrypt.gensalt()` without explicit rounds parameter
- **Fix**: Use `bcrypt.gensalt(rounds=12)` for explicit control

### Low / Informational

#### 11. Public Lookup Endpoints
- **Location**: `app/routes/auth.py:34-50` — `/zip-lookup` and `/callsign-lookup` have no `@login_required`
- **Note**: Likely intentional for public FCC data; document the decision

#### 12. Demo Mode Email Logging
- **Location**: `app/__init__.py:74` — suppressed emails logged at INFO level, exposing recipient addresses in logs
- **Fix**: Use DEBUG level instead of INFO

## Secure Areas (No Issues Found)

- **SQL injection**: All queries use parameterized `%s` placeholders across all route files
- **Authentication/authorization**: `@login_required` and `@admin_required` decorators consistently applied; ownership checks on all record and profile edit routes
- **Password hashing**: bcrypt with `checkpw()` (timing-safe)
- **TOTP**: `pyotp` with `valid_window=1`; backup codes hashed with bcrypt and marked used after redemption
- **WebAuthn**: Proper challenge-response flow, sign count validation prevents replay
- **Email**: No header injection vectors; addresses sourced from config/DB only
- **No file upload or path traversal** vectors present
- **Dependencies**: All packages at current stable versions as of review date
