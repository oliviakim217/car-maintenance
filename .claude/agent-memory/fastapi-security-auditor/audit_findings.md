---
name: Audit Findings Log
description: Per-audit record of security issues found, their severity, and fix status
type: project
---

## Audit 1 — 2026-05-03 (Full codebase, feature/airtable-integration branch)

### Critical
- C1: No authentication on any endpoint (all 4 routes unauthenticated write access)
- C2: No rate limiting on write endpoints (POST /api/mileage, POST /api/tasks/{task_id}/complete)

### High
- H1: `notes` field in CompleteTaskBody has no max_length — unbounded string forwarded to Airtable
- H2: `km` fields have no upper bound — no ceiling on mileage values written to Airtable
- H3: Validation pipeline violated — date parsing and km range checks done in route handler, not Pydantic layer
- H4: `extra='forbid'` missing on AddMileageBody and CompleteTaskBody — extra fields silently ignored

### Medium
- M1: `task_id` path parameter not validated against an allowlist or pattern before Airtable lookup
- M2: Route handlers missing BEGIN:/END: logging markers (service layer has them, routes do not)
- M3: `done_date` and `date` string fields have no max_length constraint in Pydantic models
- M4: `uvicorn` runs with `reload=True` hardcoded in __main__ block — should be env-controlled
- M5: FastAPI app exposes `/docs` and `/redoc` OpenAPI endpoints in prod (default behavior)
- M6: `categoryBadge()` in dashboard.html injects `cat` into a CSS class name without full sanitization (partial: replaces non-alpha, but XSS via class injection possible in edge cases)

### Low / Informational
- L1: `logging.level` config value read from YAML but APP_LOG_LEVEL env var overrides it — YAML value is ignored
- L2: prod and dev configs are identical except log level — prod has no stricter limits
- L3: config_loader logs the full config file path — low risk but leaks directory structure if logs are exposed

### Status
All findings confirmed fixed as of 2026-05-03 re-audit (C1, C2, H1, H2, H3, H4, M1, M2, M3, M4, M5, M6 all resolved per user). L1, L2, L3 carry-forward status unknown — not re-flagged.

---

## Audit 2 — 2026-05-03 (Full re-audit, feature/airtable-integration branch)

Confirmed previously fixed: C1, C2, H1, H2, H3, H4, M1, M2, M3, M4, M5, M6.

### High (new)
- H-NEW-1: API key exposed in HTML page source via Jinja2 `{{ api_key }}` template render in dashboard.html — any user who views page source can read the key (main.py:122, dashboard.html:146)
- H-NEW-2: Docker container runs as root (no USER instruction in Dockerfile) — container escape gives full root access to host
- H-NEW-3: No security response headers anywhere — missing X-Content-Type-Options, X-Frame-Options, Content-Security-Policy; no middleware added

### Medium (new)
- M-NEW-1: Rate limiter key is raw `get_remote_address` (reads X-Forwarded-For) with no proxy trust config — attackers can spoof their IP to bypass per-IP rate limits by sending a fake X-Forwarded-For header; no ProxyFix/trusted_hosts middleware present
- M-NEW-2: Read endpoints (GET /api/mileage, GET /api/schedule) have no rate limiting — only write endpoints are limited; config has `read_requests_per_minute` defined but never enforced
- M-NEW-3: `notes` input in HTML form has no `maxlength` attribute — client-side limit matches server-side 500-char cap inconsistently (server enforces it, browser does not hint at it); minor UX/defense-in-depth gap
- M-NEW-4: `task.status` from API response is interpolated directly into a CSS class in dashboard.html (`status-${task.status}`) with no escaping — if a malicious value ever reaches the frontend it would inject into the DOM class attribute; low real risk today since status is a server-side enum but is not escaped before use

### Low / Informational (new)
- L-NEW-1: Dockerfile has no HEALTHCHECK instruction — orchestrators cannot detect unhealthy containers
- L-NEW-2: `config_loader.py` logs the full filesystem path to the config file at INFO level on every cold start — leaks server directory layout if logs are ever exposed
- L-NEW-3: `auth.py` compares API keys with `key != expected` (Python string equality) instead of `hmac.compare_digest` — theoretically vulnerable to timing oracle attacks; low practical risk for a single-user local app but not production-hardened
- L-NEW-4: `TaskResult` output model does not use `extra='forbid'` or `extra='ignore'` — if Airtable ever returns unexpected fields they pass through to the API response; low risk but violates defense-in-depth

### Status
H-NEW-1 FIXED: API key removed from HTML. Session-based auth replaces API key; no secret in page source.
H-NEW-2 OPEN: Dockerfile still has no USER instruction — container runs as root.
H-NEW-3 OPEN: No security response headers middleware added (X-Content-Type-Options, X-Frame-Options, CSP).
M-NEW-1 FIXED: limiter.py now uses `request.client.host` (TCP IP, not X-Forwarded-For). IP spoofing via header no longer possible.
M-NEW-2 OPEN: GET endpoints still have no rate limiting. `read_requests_per_minute` in config but not enforced.
M-NEW-3 OPEN: HTML notes input still has no `maxlength` attribute. Server enforces 500 chars; browser has no hint.
M-NEW-4 OPEN (partially): `task.status` still interpolated into CSS class (`status-${task.status}`) without escaping. Real risk remains low (server enum). `task.id` is now escaped via `safeId = escapeHtml(task.id)` but status is not.
L-NEW-1 OPEN: No HEALTHCHECK in Dockerfile.
L-NEW-2 OPEN: config_loader logs full filesystem path at INFO level.
L-NEW-3 FIXED: auth.py now uses `hmac.compare_digest` for password comparison.
L-NEW-4 OPEN: TaskResult output model has no `extra='forbid'`/`extra='ignore'`.

---

## Audit 3 — 2026-05-06 (Pre-deployment, feature/docker-deployment branch)

### Previously unfixed issues confirmed still open:
- H-NEW-2: Dockerfile no USER instruction (root)
- H-NEW-3: No security response headers
- M-NEW-2: GET endpoints unrated
- M-NEW-3: Notes input no maxlength HTML attribute
- M-NEW-4: task.status unescaped in CSS class interpolation
- L-NEW-1: No HEALTHCHECK in Dockerfile
- L-NEW-2: config_loader logs full path
- L-NEW-4: TaskResult no extra='ignore'

### New findings (Audit 3):
- A-NEW-1 (Medium): SessionMiddleware `max_age` defaults to 14 days (1209600 seconds) — not explicitly set; no explicit session expiry configured for production hardening.
- A-NEW-2 (Low): `safeId` is HTML-escaped for text contexts but is also embedded in `onclick` JS attributes (`onclick="toggleTaskDetail('${safeId}')"`) — HTML entity encoding (e.g., `&#39;`) does not protect against JS string breaking in attribute context. If task_id contained a single-quote it would break the JS call. In practice the server enforces `^[a-z0-9_]{1,64}$` so single-quotes are impossible — but this is not enforced at the HTML layer.
- A-NEW-3 (Low): `notes` field on `done-notes-${safeId}` HTML input has no `maxlength` attribute — minor defense-in-depth gap (server enforces 500, browser does not).
- A-NEW-4 (Low): The `TaskResult` model uses `**task` spread in `compute_status()` — if Airtable returns unexpected fields, they are forwarded to the API response via the model. `extra='ignore'` would suppress this silently; without it, Pydantic v2 default behavior passes them through.

### Status
Reported to user 2026-05-06. Unfixed items from Audit 2 carry forward.
