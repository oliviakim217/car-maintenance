"""Schedule service module.

Handles loading, saving, and computing the status of maintenance tasks.
"""

import json
import logging
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from dateutil.relativedelta import relativedelta

from backend.modules.schedule.models import TaskResult, TaskStatus

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TASKS_FILE = _PROJECT_ROOT / "data" / "tasks.json"


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------


def load_tasks() -> List[Dict]:
    """Read data/tasks.json and return the list of task dicts.

    Returns:
        List of raw task dicts as stored in tasks.json.

    Raises:
        FileNotFoundError: If tasks.json does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    with open(_TASKS_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("tasks", [])


def _load_full_data() -> Dict:
    """Read the full tasks.json structure including the vehicle key."""
    with open(_TASKS_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_tasks(tasks: List[Dict]) -> None:
    """Persist the task list back to data/tasks.json.

    Preserves the top-level 'vehicle' object.

    Args:
        tasks: The full list of task dicts to write.

    Raises:
        IOError: If the file cannot be written.
    """
    data = _load_full_data()
    data["tasks"] = tasks
    with open(_TASKS_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------


def _resolve_next_due_date(last_done_date_str: str, interval_months: int) -> date:
    """Compute the next due date from a last-done date and a month interval.

    Args:
        last_done_date_str: ISO date string for the last service date.
        interval_months: Number of months between services.

    Returns:
        The next due date as a date object.
    """
    last = date.fromisoformat(last_done_date_str)
    return last + relativedelta(months=interval_months)


def compute_status(task: Dict, current_km: int, current_date: date, cfg) -> TaskResult:
    """Compute scheduling status for a single maintenance task.

    Derives next_due_km and/or next_due_date from the task's interval fields,
    then classifies the task as never_done, overdue, due_soon, or ok.

    Args:
        task: Raw task dict from tasks.json.
        current_km: Current estimated odometer reading in km.
        current_date: Today's date.
        cfg: AppConfig instance (for due-soon buffer values).

    Returns:
        TaskResult with all raw fields plus computed status and due fields.
    """
    last_done_km: Optional[int] = task.get("last_done_km")
    last_done_date: Optional[str] = task.get("last_done_date")
    interval_km: Optional[int] = task.get("interval_km")
    interval_months: Optional[int] = task.get("interval_months")

    # Guard: never done
    if last_done_km is None and last_done_date is None:
        return TaskResult(
            **task,
            status=TaskStatus.never_done,
        )

    next_due_km: Optional[int] = None
    next_due_date: Optional[date] = None
    km_remaining: Optional[int] = None
    days_remaining: Optional[int] = None

    if last_done_km is not None and interval_km is not None:
        next_due_km = last_done_km + interval_km
        km_remaining = next_due_km - current_km

    if last_done_date is not None and interval_months is not None:
        next_due_date = _resolve_next_due_date(last_done_date, interval_months)
        days_remaining = (next_due_date - current_date).days

    # Determine status — overdue takes priority over due_soon
    km_overdue = next_due_km is not None and current_km >= next_due_km
    date_overdue = next_due_date is not None and current_date >= next_due_date

    if km_overdue or date_overdue:
        status = TaskStatus.overdue
    else:
        buf_km = cfg.mileage.due_soon_buffer_km
        buf_days = cfg.mileage.due_soon_buffer_days
        km_due_soon = km_remaining is not None and km_remaining <= buf_km
        days_due_soon = days_remaining is not None and days_remaining <= buf_days

        if km_due_soon or days_due_soon:
            status = TaskStatus.due_soon
        else:
            status = TaskStatus.ok

    return TaskResult(
        **task,
        status=status,
        next_due_km=next_due_km,
        next_due_date=next_due_date,
        km_remaining=km_remaining,
        days_remaining=days_remaining,
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def get_all_tasks(current_km: int, current_date: date, cfg) -> List[TaskResult]:
    """Load all tasks and compute their status against the current odometer/date.

    Args:
        current_km: Current estimated odometer reading in km.
        current_date: Today's date.
        cfg: AppConfig instance.

    Returns:
        List of TaskResult objects with computed status fields.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:get_all_tasks current_km={current_km} current_date={current_date}")
    try:
        tasks = load_tasks()
        results = [compute_status(t, current_km, current_date, cfg) for t in tasks]
        logger.info(
            f"END:get_all_tasks count={len(results)} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        return results
    except Exception as exc:
        logger.error(
            f"ERROR:get_all_tasks error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise
    finally:
        pass


def mark_task_done(task_id: str, done_km: int, done_date: date) -> None:
    """Update a task's last_done_km and last_done_date fields in tasks.json.

    Args:
        task_id: The 'id' field of the task to update.
        done_km: Odometer reading when the task was completed.
        done_date: Calendar date when the task was completed.

    Raises:
        ValueError: If no task with the given id is found.
        IOError: If tasks.json cannot be read or written.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:mark_task_done task_id={task_id} done_km={done_km} done_date={done_date}")
    try:
        tasks = load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["last_done_km"] = done_km
                task["last_done_date"] = done_date.isoformat()
                save_tasks(tasks)
                logger.info(
                    f"END:mark_task_done task_id={task_id} "
                    f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
                )
                return

        raise ValueError(f"Task not found: {task_id}")
    except Exception as exc:
        logger.error(
            f"ERROR:mark_task_done task_id={task_id} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise
    finally:
        pass


