---
applyTo: "**"
---

# Scalability and Extension Contract
# Version: 1.1.0
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

## Vendor-Swappable Capabilities (Placeholder Pattern)

Some capabilities are likely to change vendors later even if only one implementation exists
today — the vector store behind `manual_qa` is the current example (local `.npy` files today;
could become Pinecone, Qdrant, or pgvector later). For these, add the placeholder seam NOW,
before a second vendor exists, so the future swap is additive instead of a rewrite.

### Identify a vendor-swappable capability
→ Ask: "if I switched providers for this, would business logic need to change?" If yes, it
  needs a placeholder interface now.
→ Current example: vector search in `manual_qa_service.py` (`_search_manual_chunks` calling
  `numpy` directly against `embeddings.npy`) is a vendor-swappable capability with only one
  vendor — "local file" — implemented so far.

### Add the placeholder interface
→ Create a dedicated service file: `backend/services/<capability>_service.py`
  (e.g. `vector_store_service.py`) — this is the ONLY file allowed to know which vendor is
  active.
→ Expose vendor-agnostic function signatures only, e.g.:
   - `vector_store_search(query_embedding: np.ndarray, top_k: int) -> list[dict]`
   - `vector_store_upsert(chunks: list[dict]) -> None`
→ Move the current implementation behind that interface even though there is only one vendor —
  do not wait for a second vendor to justify the seam.
→ Business logic (e.g. `manual_qa_service.py`) calls only these functions — never a vendor SDK,
  `numpy`, or a file path directly.
→ Which implementation is active is chosen by config (`vector_store.provider` in
  `config.yaml`), never hardcoded — see `Config Files` rules in `CLAUDE.md`.

### Swap or add a vendor later
→ Add a new implementation module (e.g. `backend/services/vector_store_pinecone.py`) satisfying
  the same interface.
→ Add the new vendor's prefix to the External Service Prefix Contract table in
  `naming-rules.md` before writing code (e.g. `pinecone_`, `PINECONE_`, `PineconeConfig`).
→ Point config at the new provider.
→ Zero changes to `manual_qa_service.py`, routes, or any other consumer of the interface.

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
