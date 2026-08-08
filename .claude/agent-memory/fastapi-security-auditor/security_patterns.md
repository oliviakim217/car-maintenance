---
name: Codebase Security Patterns
description: Recurring security patterns, Airtable formula usage, Pydantic model config, auth posture, and injection risk areas in this codebase
type: project
---

## Airtable Formula Construction
- All Airtable lookups use `pyairtable.formulas.match({"task_id": task_id})` — this is the safe parameterized helper, not raw string interpolation. Correct as of 2026-05-03 audit.
- Field names used in `match()` calls: `task_id` (hardcoded string literal, not user-supplied). Safe.
- Mileage sort uses `sort=["-date"]` — hardcoded, safe.

## Pydantic Models (as of Audit 2, 2026-05-03)
- `AddMileageBody` (mileage_routes.py): Has `extra='forbid'`, `Field(gt=0, le=999_999)` on km, `max_length=10` on date, `@field_validator` for date format. Fully hardened.
- `CompleteTaskBody` (schedule_routes.py): Has `extra='forbid'`, `Field(gt=0, le=999_999)` on done_km, `max_length=10` on done_date, `max_length=500` on notes, `@field_validator` for date format. Fully hardened.
- `TaskResult` (models.py): Output model only. No `extra='forbid'`/`extra='ignore'` set — unexpected Airtable fields pass through. Low risk but noted.
- Config models (config_loader.py): No `extra='forbid'` — acceptable since source is controlled YAML, not user input.

## Authentication & Authorization (as of Audit 2)
- `require_api_key` dependency added to both routers via `router = APIRouter(dependencies=[Depends(require_api_key)])`. All 4 endpoints are now protected.
- Auth uses Python string equality (`key != expected`), not `hmac.compare_digest` — minor timing oracle risk.
- API key is passed to dashboard.html as a Jinja2 template variable (`{{ api_key }}`) and embedded in page source — any user who views source can read the key. HIGH severity finding.

## Secrets & Config
- Secrets correctly stored in .env only. YAML configs contain no credentials.
- .env is in .gitignore and .dockerignore. Correct.
- AIRTABLE_TOKEN checked for presence in _get_api() before use.
- APP_API_KEY embedded in HTML page source via Jinja2 template — secret leaks to browser. HIGH.

## Logging
- BEGIN:/END:/ERROR: markers now present in both service layer and route handlers.
- No passwords, tokens, or secrets are logged.
- config_loader logs full filesystem path at INFO level on cold start — leaks directory structure if logs are exposed.

## Rate Limiting (as of Audit 2)
- `@limiter.limit(lambda: ...)` applied to POST /api/mileage and POST /api/tasks/{task_id}/complete only.
- GET /api/mileage and GET /api/schedule have NO rate limiting despite `read_requests_per_minute` being defined in config.
- Rate limiter uses `get_remote_address` which trusts X-Forwarded-For header. No proxy trust middleware (ProxyFix/TrustedHosts) configured — IP spoofing bypasses rate limits.

## Security Headers & CORS
- No CORS middleware configured.
- No security response headers (X-Content-Type-Options, X-Frame-Options, Content-Security-Policy, etc.) added anywhere.

## Container Security
- Dockerfile has no USER instruction — container runs as root.
- No HEALTHCHECK instruction in Dockerfile.

## Input Validation Pipeline
- Pipeline order correct: Pydantic → validator → service. Pipeline violation from Audit 1 resolved.
- `task.status` from API is interpolated into CSS class in dashboard.html without escaping — low real risk since status is a server enum, but not escaped.
- HTML notes inputs have no `maxlength` attribute — server enforces 500 chars but browser has no matching hint.
- `task.id` is HTML-escaped as `safeId` before use in DOM IDs and `onclick` attributes. The server enforces `^[a-z0-9_]{1,64}$` so the escaping is belt-and-suspenders.

## Session Management (as of Audit 3, 2026-05-06)
- SessionMiddleware configured with `same_site="lax"`, `https_only=(env=="prod")`. Correct.
- `max_age` not explicitly set — defaults to 14 days (1,209,600 seconds). No explicit session expiry override for production.
- Session contains only `{"authenticated": True}` — no user-specific data, no privilege escalation risk.
- `hmac.compare_digest` used for password comparison in auth_routes.py. Timing-safe.
- No API key in HTML page source — H-NEW-1 confirmed fixed.

## Rate Limiting (as of Audit 3, 2026-05-06)
- M-NEW-1 FIXED: limiter.py now uses `request.client.host` (TCP IP, not X-Forwarded-For). IP spoofing no longer possible.
- GET endpoints (GET /api/mileage, GET /api/schedule) still have NO rate limiting. `read_requests_per_minute` in config but unused.
- Write rate limits applied correctly to POST /api/mileage and POST /api/tasks/{task_id}/complete.
- /login rate limited at hardcoded "5/minute" — not config-driven. Low risk but inconsistency.

## Container Security (as of Audit 3, 2026-05-06)
- Dockerfile still has no USER instruction — container runs as root.
- No HEALTHCHECK instruction.
- .dockerignore correctly excludes .env, .git, tests/, .claude/, venv/.
- CMD uses `--host 0.0.0.0` which is correct for container networking.

## Dashboard Scan Feature (as of Audit 4, 2026-08-08)
- Auth: router uses `dependencies=[Depends(require_session)]` — all endpoints including upload are session-protected. Correct.
- Rate limiting: `@limiter.limit(lambda: ...)` applied to upload endpoint using write_requests_per_minute from config. Correct.
- File type validation: `file.content_type` is user-controlled HTTP header — checked against allowlist AFTER read, not verified against actual file magic bytes. Attacker can upload arbitrary file as image/jpeg.
- File size: validated in dashboard_service.py against config value after full read into memory — DoS risk if max_image_size_mb is large. No streaming read or FastAPI max-size limit set before buffering.
- media_type passed to Anthropic API verbatim from user-controlled header (after allowlist check). Allowlist check in dashboard_service is the sole guard.
- `int(raw_text.replace(",", "").replace(" ", ""))` on Claude response: safe for ValueError (raised then re-raised), but IndexError on empty `message.content` is unguarded.
- `message.content[0].text` accessed without guarding against empty list — IndexError would propagate as HTTP 500 (safe for user, but improper).
- No logging scrub filter in main.py — CLAUDE.md requires one (Bearer/pat/Authorization/password scrubber). Still missing.
- Security headers middleware (_SecurityHeadersMiddleware) is NOW present in main.py — H-NEW-3 from Audit 2 is FIXED.
- GET endpoints still have no rate limiting (carry-forward from Audit 2/3).
- Dockerfile USER instruction and HEALTHCHECK status not re-verified in Audit 4.
- `int()` parse: `raw_text` after replace could still be non-numeric if Claude produces unexpected output (e.g., negative sign, decimal, scientific notation) — int("-1") succeeds and passes plausibility check; int("1e5") raises ValueError (caught). Negative values would fail plausibility (min_km_plausible=1000).
- Prompt injection via image metadata: no real attack surface — image bytes are sent as base64 data, not parsed text. Metadata fields (EXIF) are not extracted and injected into the prompt. Low risk.
- Model name comes from config (cfg_scan.model), not user input. Safe.
- ANTHROPIC_API_KEY read from env at call time, not cached — correct. Not logged.
- Log in route logs `file.content_type` (user-controlled) at INFO — value is bounded by allowlist check downstream; leaks user-supplied string to logs, but at INFO not ERROR, and no secret data.
