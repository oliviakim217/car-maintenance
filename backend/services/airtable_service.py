"""Airtable service module.

Provides all CRUD operations for the three Airtable tables used by this app:
  - Tasks          — maintenance task definitions and last-done tracking
  - Mileage        — odometer reading history
  - Maintenance Log — completed task audit log

Authentication uses AIRTABLE_TOKEN from the environment.
The base ID is resolved from AIRTABLE_BASE_ID_DEV or AIRTABLE_BASE_ID_PROD
based on the APP_ENV environment variable.

Expected field names per table
-------------------------------
Tasks:
  task_id (text), name (text), category (text), interval_km (number),
  interval_months (number), notes (long text), last_done_km (number),
  last_done_date (text — ISO date, e.g. "2026-03-28")

Mileage:
  date (text — ISO date), km (number), type (text — "manual")

Maintenance Log:
  date (text — ISO date), task_name (text), km (number), notes (long text)
"""

import logging
import os
import time
from datetime import date
from typing import Dict, List, Optional

from pyairtable import Api
from pyairtable.formulas import match

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_api() -> Api:
    """Build and return an authenticated Airtable API client.

    Raises:
        RuntimeError: If AIRTABLE_TOKEN is not set.
    """
    token = os.getenv("AIRTABLE_TOKEN")
    if not token:
        raise RuntimeError("AIRTABLE_TOKEN environment variable is not set")
    return Api(token)


def _resolve_base_id() -> str:
    """Return the Airtable base ID for the current APP_ENV.

    Raises:
        RuntimeError: If the required env var is not set.
    """
    app_env = os.getenv("APP_ENV", "dev")
    env_key = f"AIRTABLE_BASE_ID_{app_env.upper()}"
    base_id = os.getenv(env_key)
    if not base_id:
        raise RuntimeError(f"{env_key} environment variable is not set")
    return base_id


def _get_table(table_name: str):
    """Return a pyairtable Table object for the given table name."""
    api = _get_api()
    base_id = _resolve_base_id()
    return api.table(base_id, table_name)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


def get_all_task_dicts(table_name: str) -> List[Dict]:
    """Fetch all records from the Tasks table and return as plain dicts.

    Each returned dict mirrors the fields from tasks.json (task_id, name,
    category, interval_km, interval_months, notes, last_done_km,
    last_done_date).

    Args:
        table_name: Airtable table name for tasks.

    Returns:
        List of task dicts with field values, excluding Airtable metadata.

    Raises:
        RuntimeError: If Airtable credentials are not configured.
        Exception: On network or API errors.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:get_all_task_dicts table={table_name}")
    try:
        table = _get_table(table_name)
        records = table.all()
        tasks = [record["fields"] for record in records]
        logger.info(
            f"END:get_all_task_dicts table={table_name} count={len(tasks)} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        return tasks
    except Exception as exc:
        logger.error(
            f"ERROR:get_all_task_dicts table={table_name} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


def update_task_done(
    table_name: str,
    task_id: str,
    done_km: int,
    done_date: date,
) -> None:
    """Update last_done_km and last_done_date for a task identified by task_id.

    Args:
        table_name: Airtable table name for tasks.
        task_id: The value of the task_id field (e.g. "engine_oil_filter").
        done_km: Odometer reading at time of completion.
        done_date: Calendar date of completion.

    Raises:
        ValueError: If no record with the given task_id is found.
        RuntimeError: If Airtable credentials are not configured.
        Exception: On network or API errors.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:update_task_done task_id={task_id} done_km={done_km} done_date={done_date}")
    try:
        table = _get_table(table_name)
        record = table.first(formula=match({"task_id": task_id}))
        if record is None:
            raise ValueError(f"Task not found in Airtable: {task_id}")
        table.update(
            record["id"],
            {
                "last_done_km": done_km,
                "last_done_date": done_date.isoformat(),
            },
        )
        logger.info(
            f"END:update_task_done task_id={task_id} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:update_task_done task_id={task_id} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


def get_task_dict(table_name: str, task_id: str) -> Optional[Dict]:
    """Fetch a single task dict by task_id, or None if not found.

    Args:
        table_name: Airtable table name for tasks.
        task_id: The value of the task_id field.

    Returns:
        Task field dict, or None if no matching record exists.

    Raises:
        RuntimeError: If Airtable credentials are not configured.
        Exception: On network or API errors.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:get_task_dict task_id={task_id}")
    try:
        table = _get_table(table_name)
        record = table.first(formula=match({"task_id": task_id}))
        result = record["fields"] if record else None
        logger.info(
            f"END:get_task_dict task_id={task_id} found={result is not None} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        return result
    except Exception as exc:
        logger.error(
            f"ERROR:get_task_dict task_id={task_id} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


# ---------------------------------------------------------------------------
# Mileage
# ---------------------------------------------------------------------------


def get_last_mileage_entry(table_name: str) -> Dict:
    """Return the most recent odometer entry from the Mileage table.

    Entries are sorted by the 'date' field descending; the first result
    is the most recent reading.

    Args:
        table_name: Airtable table name for mileage entries.

    Returns:
        Dict with keys 'date' (ISO string), 'km' (int), 'type' (str).

    Raises:
        ValueError: If the Mileage table has no entries.
        RuntimeError: If Airtable credentials are not configured.
        Exception: On network or API errors.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:get_last_mileage_entry table={table_name}")
    try:
        table = _get_table(table_name)
        record = table.first(sort=["-date"])
        if record is None:
            raise ValueError("No mileage entries found in Airtable")
        entry = record["fields"]
        logger.info(
            f"END:get_last_mileage_entry date={entry.get('date')} km={entry.get('km')} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        return entry
    except Exception as exc:
        logger.error(
            f"ERROR:get_last_mileage_entry table={table_name} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


def add_mileage_entry(table_name: str, km: int, entry_date: date) -> None:
    """Append a new manual odometer reading to the Mileage table.

    Args:
        table_name: Airtable table name for mileage entries.
        km: Odometer value in kilometres.
        entry_date: Date of the reading.

    Raises:
        RuntimeError: If Airtable credentials are not configured.
        Exception: On network or API errors.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:add_mileage_entry km={km} date={entry_date}")
    try:
        table = _get_table(table_name)
        table.create({"date": entry_date.isoformat(), "km": km, "type": "manual"})
        logger.info(
            f"END:add_mileage_entry km={km} date={entry_date} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:add_mileage_entry km={km} date={entry_date} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


# ---------------------------------------------------------------------------
# Maintenance Log
# ---------------------------------------------------------------------------


def append_maintenance_log(
    table_name: str,
    task_name: str,
    done_km: int,
    done_date: date,
    notes: str,
) -> None:
    """Append a completed-task record to the Maintenance Log table.

    This is a non-critical write — callers should catch and log failures
    rather than propagating them to the user.

    Args:
        table_name: Airtable table name for the maintenance log.
        task_name: Human-readable task name.
        done_km: Odometer reading at time of completion.
        done_date: Calendar date of completion.
        notes: Any additional notes to record.

    Raises:
        RuntimeError: If Airtable credentials are not configured.
        Exception: On network or API errors.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:append_maintenance_log task={task_name!r} km={done_km} date={done_date}")
    try:
        table = _get_table(table_name)
        table.create(
            {
                "date": done_date.isoformat(),
                "task_name": task_name,
                "km": done_km,
                "notes": notes,
            }
        )
        logger.info(
            f"END:append_maintenance_log task={task_name!r} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:append_maintenance_log task={task_name!r} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise
