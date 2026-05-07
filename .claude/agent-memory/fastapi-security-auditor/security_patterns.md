---
name: Codebase Security Patterns
description: Recurring security patterns, Airtable formula usage, Pydantic model config, auth posture, and injection risk areas in this codebase
type: project
---

## Airtable Formula Construction
- All Airtable lookups use `pyairtable.formulas.match({"task_id": task_id})` — this is the safe parameterized helper, not raw string interpolation. Correct as of 2026-05-03 audit.
- Field names used in `match()` calls: `task_id` (hardcoded string literal, not user-supplied). Safe.
- Mileage sort uses `sort=["-date"]` — hardcoded, safe.

## Pydantic Models
- `AddMileageBody` (mileage_routes.py): No `extra='forbid'`, no `max_length` on `date` str, no Field constraints on `km` (int only, no upper bound). Missing `ConfigDict`.
- `CompleteTaskBody` (schedule_routes.py): No `extra='forbid'`, no `max_length` on `notes` or `done_date` str, no upper bound on `done_km`. Missing `ConfigDict`.
- `TaskResult` (models.py): Output model only — no `extra='forbid'` needed, but `last_done_date` is `Optional[str]` with no format validation.
- Config models (config_loader.py): No `extra='forbid'` — low risk since they read from controlled YAML, not user input.

## Authentication & Authorization
- NO authentication on any endpoint. All routes are unauthenticated:
  - GET /api/mileage — read, unauthenticated
  - POST /api/mileage — write, unauthenticated
  - GET /api/schedule — read, unauthenticated
  - POST /api/tasks/{task_id}/complete — write, unauthenticated
- task_id path parameter: user-controlled, passed into Airtable match() (safe via parameterization), but no allowlist validation.

## Secrets & Config
- Secrets correctly stored in .env only. YAML configs contain no credentials.
- .env is in .gitignore. Correct.
- AIRTABLE_TOKEN checked for presence in _get_api() before use.

## Logging
- `logger.info(f"BEGIN:add_manual_reading km={km} date={reading_date}")` — logs km value before validation guard completes; low risk since km is an int.
- No passwords, tokens, or secrets are logged.
- END:/ERROR: markers present in service layer. Route layer missing BEGIN:/END: markers.

## Rate Limiting
- No rate limiting on any endpoint. No middleware observed.

## Input Validation Pipeline
- Route layer does date parsing (`date.fromisoformat`) and range checks (`km <= 0`) outside of Pydantic validators — pipeline violation (sanitization in route handler, not Pydantic layer).
- `notes` field forwarded directly to Airtable with no length cap.
- `task_id` from URL path not validated against an allowlist before Airtable lookup.
