---
name: backend-recurring-violations
description: Recurring naming-violation patterns found in backend/, plus which files are consistently clean
type: project
---

First full `backend/` audit was run 2026-08-08 (25 .py files, branch `feature/dashboard-photo-upload`). Five violation patterns recur across nearly every file:

1. **No FastAPI handler carries the `api_` prefix** except `api_upload_dashboard_photo`. All 7 other handlers (main.py, auth_routes, mileage_routes, schedule_routes) are bare verbs.
2. **Every env var read drops its service prefix** — `token`, `api_key`, `base_id`, `expected`. The rules name the correct form for each of these verbatim, so these are always Critical.
3. **Both service clients are misnamed** — `api = _get_api()` (pyairtable) and `client = anthropic.AsyncAnthropic(...)`. The contract requires `airtable_client` / `anthropic_client`.
4. **`backend/constants.py` does not exist.** Every constant is inline (`_ODOMETER_PROMPT`, `_MAGIC_SIGNATURES`, `_TASK_ID_RE`, `_PROJECT_ROOT` ×2, `max_tokens=64`). This is a structural gap, not a per-file slip.
5. **Booleans in `schedule_service.compute_status` drop `is_`** — `km_overdue`, `date_overdue`, `km_due_soon`, `days_due_soon`. Note `is_never_done` in the same function is correct, so the author knows the rule.

**Why:** These cluster by category rather than by file, so auditing category-first (all handlers, then all env reads, then all clients) finds more than reading file-by-file.

**How to apply:** On re-audit, check these five first — they are the likely regressions. Also check whether `backend/constants.py` has since been created.

**Consistently clean files** (no violations found): `backend/modules/dashboard_scan/models.py`, `backend/utils/auth.py`, `backend/modules/schedule/models.py` apart from its `id` field. `config_loader.py` class names are all correct (`AppConfig`, `AirtableConfig`, `MileageConfig`, …) — class naming is the project's strongest area.

**Highest-cascade violation:** `TaskResult.id` (models.py:27) shadows the builtin `id` and is populated in `schedule_service.py:104`. It crosses into the frontend JSON contract, so it cannot be fixed backend-only.

See [[naming-rules-gaps]] for cases where the rules themselves were ambiguous.
