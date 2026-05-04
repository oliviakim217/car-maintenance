"""Seed script — provision fields and populate Airtable tables with initial data.

Tables handled
--------------
Tasks          — creates required fields if missing, then uploads all task
                 definitions from data/tasks.json (idempotent by task_id)
Mileage        — creates required fields if missing, then adds one seed entry
                 if the table is empty
Maintenance Log — creates required fields if missing; data is left empty
                  (append-only log; nothing to seed)

Usage
-----
    # Full run: provision fields + seed data (token needs schema.bases:write)
    APP_ENV=dev python scripts/seed_airtable.py

    # Seed-only: skip field provisioning (fields must already exist)
    APP_ENV=dev python scripts/seed_airtable.py --seed-only

Token scopes required
---------------------
- data.records:read  — check for existing rows
- data.records:write — create rows
- schema.bases:read  — read existing field names (full run only)
- schema.bases:write — create missing fields   (full run only)

If your token lacks schema access, run with --seed-only after creating
fields manually (see the FIELD REFERENCE printed on a 403 error).

The script is safe to re-run: existing fields and task records are skipped,
not duplicated.

Prerequisites
-------------
- AIRTABLE_TOKEN, AIRTABLE_BASE_ID_DEV (or _PROD) must be set in .env or
  the shell environment.
- The three Airtable tables must already exist (empty tables are fine).
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap: resolve project root and load .env before any other imports
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from pyairtable import Api  # noqa: E402 (must be after dotenv load)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TASKS_JSON_PATH = PROJECT_ROOT / "data" / "tasks.json"

# Seed mileage: most recent known reading derived from task history.
SEED_MILEAGE_KM = 48925
SEED_MILEAGE_DATE = "2026-04-05"

# ---------------------------------------------------------------------------
# Field definitions
# Field type strings are Airtable API field type identifiers.
# Each entry: (field_name, field_type)
# ---------------------------------------------------------------------------

TASKS_FIELDS: List[Dict] = [
    {"name": "task_id", "type": "singleLineText"},
    {"name": "name", "type": "singleLineText"},
    {"name": "category", "type": "singleLineText"},
    {"name": "interval_km", "type": "number", "options": {"precision": 0}},
    {"name": "interval_months", "type": "number", "options": {"precision": 0}},
    {"name": "notes", "type": "multilineText"},
    {"name": "last_done_km", "type": "number", "options": {"precision": 0}},
    {"name": "last_done_date", "type": "singleLineText"},
]

MILEAGE_FIELDS: List[Dict] = [
    {"name": "date", "type": "singleLineText"},
    {"name": "km", "type": "number", "options": {"precision": 0}},
    {"name": "type", "type": "singleLineText"},
]

MAINTENANCE_LOG_FIELDS: List[Dict] = [
    {"name": "date", "type": "singleLineText"},
    {"name": "task_name", "type": "singleLineText"},
    {"name": "km", "type": "number", "options": {"precision": 0}},
    {"name": "notes", "type": "multilineText"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_table(table_name: str):
    """Return a pyairtable Table for the current APP_ENV."""
    token = os.getenv("AIRTABLE_TOKEN")
    if not token:
        raise RuntimeError("AIRTABLE_TOKEN is not set")

    app_env = os.getenv("APP_ENV", "dev")
    base_id_key = f"AIRTABLE_BASE_ID_{app_env.upper()}"
    base_id = os.getenv(base_id_key)
    if not base_id:
        raise RuntimeError(f"{base_id_key} is not set")

    api = Api(token)
    return api.table(base_id, table_name)


def _load_tasks() -> list:
    """Load and return the task list from tasks.json."""
    with open(TASKS_JSON_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data["tasks"]


_FIELD_REFERENCE = """
FIELD REFERENCE — create these fields manually in Airtable, then re-run with --seed-only.

  Tasks table
  -----------
  task_id         Single line text
  name            Single line text
  category        Single line text
  interval_km     Number (precision: 0)
  interval_months Number (precision: 0)
  notes           Long text
  last_done_km    Number (precision: 0)
  last_done_date  Single line text

  Mileage table
  -------------
  date  Single line text
  km    Number (precision: 0)
  type  Single line text

  Maintenance Log table
  ---------------------
  date       Single line text
  task_name  Single line text
  km         Number (precision: 0)
  notes      Long text
"""


def _normalize(name: str) -> str:
    """Normalize a field name for fuzzy matching: lowercase, strip spaces and underscores.

    Examples:
        "Interval KM"  -> "intervalkm"
        "interval_km"  -> "intervalkm"
        "Last Done Date" -> "lastdonedate"
    """
    return name.lower().replace(" ", "").replace("_", "")


def _rename_field(table, field_id: str, new_name: str) -> None:
    """Rename an existing Airtable field via the metadata PATCH endpoint.

    Args:
        table: pyairtable Table instance.
        field_id: The Airtable field ID (e.g. "fldXXXXXX").
        new_name: The new field name.
    """
    table.api.patch(table.meta_url("fields", field_id), json={"name": new_name})


def _provision_fields(table, field_specs: List[Dict]) -> None:
    """Ensure all required fields exist on the table with the exact expected names.

    Strategy per required field:
    - Exact match found       → skip (already correct).
    - Normalized match found  → rename the existing field to the expected name.
      Normalization strips spaces and underscores and lowercases, so
      "Interval KM" matches "interval_km", "Last Done Date" matches
      "last_done_date", etc.
    - No match found          → create a new field.

    Args:
        table: pyairtable Table instance.
        field_specs: List of dicts with keys: name, type, and optional options.

    Raises:
        PermissionError: If the token lacks schema.bases:write scope (HTTP 403).
        Exception: On other network or API errors.
    """
    try:
        schema = table.schema()
    except Exception as exc:
        if "403" in str(exc):
            logger.error(
                "provision_fields failed: token lacks schema.bases:read/write scope. "
                "Grant schema.bases:write in Airtable → Personal Access Tokens, "
                "or create fields manually and re-run with --seed-only."
            )
            print(_FIELD_REFERENCE)
            raise PermissionError(
                "Token missing schema.bases:write. See field reference above."
            ) from exc
        raise

    # Build lookup maps: exact name → field, and normalized name → field.
    exact_map = {f.name: f for f in schema.fields}
    normalized_map = {_normalize(f.name): f for f in schema.fields}
    logger.info(f"provision_fields table={table.name} existing={sorted(exact_map)}")

    for spec in field_specs:
        field_name = spec["name"]

        if field_name in exact_map:
            logger.info(f"provision_fields skip field={field_name!r} (exact match)")
            continue

        normalized_target = _normalize(field_name)
        if normalized_target in normalized_map:
            existing_field = normalized_map[normalized_target]
            _rename_field(table, existing_field.id, field_name)
            logger.info(
                f"provision_fields renamed field={existing_field.name!r} -> {field_name!r}"
            )
            continue

        options = spec.get("options")
        table.create_field(name=field_name, type=spec["type"], options=options)
        logger.info(f"provision_fields created field={field_name!r} type={spec['type']}")


# ---------------------------------------------------------------------------
# Setup + Seed: Tasks
# ---------------------------------------------------------------------------


def setup_and_seed_tasks(table_name: str, seed_only: bool = False) -> None:
    """Provision fields and upload all tasks from tasks.json.

    Skips any task_id that already exists in the table.

    Args:
        table_name: Airtable table name for tasks.
        seed_only: If True, skip field provisioning.
    """
    logger.info(f"BEGIN:setup_and_seed_tasks table={table_name} seed_only={seed_only}")
    start_ms = time.monotonic()

    try:
        tasks = _load_tasks()
        table = _get_table(table_name)

        if not seed_only:
            _provision_fields(table, TASKS_FIELDS)

        # Fetch existing task_ids to skip duplicates.
        existing_records = table.all(fields=["task_id"])
        existing_ids = {r["fields"].get("task_id") for r in existing_records}
        logger.info(f"setup_and_seed_tasks existing_task_count={len(existing_ids)}")

        to_create = []
        for task in tasks:
            task_id = task.get("id")
            if task_id in existing_ids:
                logger.info(f"setup_and_seed_tasks skip task_id={task_id} (already exists)")
                continue

            fields = {
                "task_id": task_id,
                "name": task["name"],
                "category": task["category"],
                "notes": task.get("notes", ""),
            }
            if task.get("interval_km") is not None:
                fields["interval_km"] = task["interval_km"]
            if task.get("interval_months") is not None:
                fields["interval_months"] = task["interval_months"]
            if task.get("last_done_km") is not None:
                fields["last_done_km"] = task["last_done_km"]
            if task.get("last_done_date") is not None:
                fields["last_done_date"] = task["last_done_date"]

            to_create.append(fields)

        if not to_create:
            logger.info("setup_and_seed_tasks nothing_to_create (all tasks already present)")
        else:
            # pyairtable batch_create handles the 10-record-per-request limit.
            table.batch_create(to_create)
            logger.info(f"setup_and_seed_tasks created_count={len(to_create)}")

        logger.info(
            f"END:setup_and_seed_tasks "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:setup_and_seed_tasks error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


# ---------------------------------------------------------------------------
# Setup + Seed: Mileage
# ---------------------------------------------------------------------------


def setup_and_seed_mileage(table_name: str, seed_only: bool = False) -> None:
    """Provision fields and add one seed mileage entry if the table is empty.

    Args:
        table_name: Airtable table name for mileage.
        seed_only: If True, skip field provisioning.
    """
    logger.info(f"BEGIN:setup_and_seed_mileage table={table_name} seed_only={seed_only}")
    start_ms = time.monotonic()

    try:
        table = _get_table(table_name)
        if not seed_only:
            _provision_fields(table, MILEAGE_FIELDS)

        existing = table.first()
        if existing is not None:
            logger.info("setup_and_seed_mileage skip (table already has entries)")
        else:
            table.create(
                {"date": SEED_MILEAGE_DATE, "km": SEED_MILEAGE_KM, "type": "manual"}
            )
            logger.info(
                f"setup_and_seed_mileage created "
                f"date={SEED_MILEAGE_DATE} km={SEED_MILEAGE_KM}"
            )

        logger.info(
            f"END:setup_and_seed_mileage "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:setup_and_seed_mileage error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


# ---------------------------------------------------------------------------
# Setup: Maintenance Log (fields only — no seed data)
# ---------------------------------------------------------------------------


def setup_maintenance_log(table_name: str, seed_only: bool = False) -> None:
    """Provision fields on the Maintenance Log table. No rows are seeded.

    Args:
        table_name: Airtable table name for the maintenance log.
        seed_only: If True, skip field provisioning.
    """
    logger.info(f"BEGIN:setup_maintenance_log table={table_name} seed_only={seed_only}")
    start_ms = time.monotonic()

    try:
        table = _get_table(table_name)
        if not seed_only:
            _provision_fields(table, MAINTENANCE_LOG_FIELDS)
        logger.info(
            f"END:setup_maintenance_log "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:setup_maintenance_log error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run field provisioning and seed operations for the configured APP_ENV."""
    parser = argparse.ArgumentParser(description="Provision Airtable fields and seed initial data.")
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Skip field provisioning; fields must already exist in Airtable.",
    )
    args = parser.parse_args()

    app_env = os.getenv("APP_ENV", "dev")
    logger.info(f"seed_airtable starting env={app_env} seed_only={args.seed_only}")

    # Import here (after sys.path is patched) to avoid import errors at the
    # module level when running outside the virtual environment.
    from backend.config.config_loader import get_config  # noqa: PLC0415

    cfg = get_config()
    tasks_table = cfg.airtable.tasks_table
    mileage_table = cfg.airtable.mileage_table
    log_table = cfg.airtable.maintenance_log_table

    setup_and_seed_tasks(tasks_table, seed_only=args.seed_only)
    setup_and_seed_mileage(mileage_table, seed_only=args.seed_only)
    setup_maintenance_log(log_table, seed_only=args.seed_only)

    logger.info("seed_airtable complete")


if __name__ == "__main__":
    main()
