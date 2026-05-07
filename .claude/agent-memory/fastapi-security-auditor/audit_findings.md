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
All findings reported to user 2026-05-03. No fixes applied yet.
