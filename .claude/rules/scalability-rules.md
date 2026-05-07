---
applyTo: "**"
---

# Scalability and Extension Contract
# Version: 1.0.0
# This file defines HOW to extend the Car Maintenance app without modifying existing code.

## Core Principle

The code itself is the LAST thing that changes.
Every extension point below requires config changes or new files — not edits to existing modules.

## Extension Patterns

### Add a new maintenance task
→ Add a row directly in the Airtable Tasks table
→ Zero code changes required
→ The task appears in the dashboard automatically on next load

### Add a new dropdown value (category, task type)
→ Edit the relevant list in config only
→ Zero code changes required

### Add a new field to a maintenance task
→ Add the field to the Airtable Tasks table schema
→ Add the field to `TaskResult` in `backend/modules/schedule/models.py`
→ Add mapping logic in `backend/modules/schedule/schedule_service.py`
→ No changes to `airtable_service.py`, `schedule_routes.py`, or `main.py`

### Add a new Airtable table (e.g. reminders, receipts)
→ Create the table in Airtable and add any seed data via `scripts/seed_airtable.py`
→ Add CRUD functions for the new table in `backend/services/airtable_service.py`
→ Create a new module folder: `backend/modules/<feature>/`
→ Add these files inside it:
   - `models.py`            — Pydantic input/output models
   - `<feature>_service.py` — business logic only, calls airtable_service
→ Create a new route file: `backend/routes/<feature>_routes.py`
→ Register the router in `backend/main.py`
→ Add any new config values to `configs/dev/config.yaml` and `configs/prod/config.yaml`
→ Do NOT modify any existing module, service, or route file

### Add a new external integration (e.g. email reminders, push notifications)
→ Create a new service file: `backend/services/<name>_service.py`
→ Credentials go in `.env` only — never in YAML or code
→ Config (rate limits, thresholds, templates) goes in YAML config
→ Do NOT modify `airtable_service.py` or any existing module

## Rules for Adding Code

1. New features go under `backend/modules/<feature_name>/`. Do not put business logic elsewhere.
2. `backend/services/airtable_service.py` is the ONLY file that calls the Airtable API.
3. New config sections go under a new top-level key in `config.yaml`.
4. New env vars use a descriptive prefix matching their service: `AIRTABLE_`, `SMTP_`, etc.
5. Follow the same pipeline: Pydantic Validate → Business Validate → Call Service → Return typed result.
6. Follow all naming conventions in `naming-rules.md`.
7. Every endpoint returns a plain dict or a typed Pydantic model — no ad-hoc response shapes.
8. Write test data files in `tests/test_data/` covering happy path and edge cases.
9. Do not modify `main.py`, `config_loader.py`, or another feature's module.

## Code Generation Checklist

Before finalizing any generated code, verify:

- [ ] Folder placement follows the structure in `CLAUDE.md`
- [ ] All config values come from YAML config — nothing is hardcoded
- [ ] Every function has type hints, a docstring, and a try/except where appropriate
- [ ] Logging uses `BEGIN:/END:/ERROR:` markers with `duration_ms` on all external calls
- [ ] Naming follows `naming-rules.md`
- [ ] Input goes through full pipeline: Pydantic → business validation → service call
- [ ] Code is testable without modifying `main.py`
- [ ] No `print()` statements anywhere
- [ ] No secrets, tokens, or URLs hardcoded anywhere
- [ ] `requests` library is not used — `httpx` only
