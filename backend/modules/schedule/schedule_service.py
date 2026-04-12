"""Schedule service module.

Handles loading tasks from Airtable, computing maintenance status, and
recording task completions.
"""

import logging
import time
from datetime import date
from typing import Dict, List, Optional

from dateutil.relativedelta import relativedelta

from backend.modules.schedule.models import TaskResult, TaskStatus
from backend.services.airtable_service import get_all_task_dicts, get_task_dict, update_task_done

logger = logging.getLogger(__name__)


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
        task: Task dict with fields matching the Airtable Tasks table schema.
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

    is_never_done = last_done_km is None and last_done_date is None

    # For never-done tasks use vehicle initial values as the baseline so that
    # km_remaining and days_remaining are still computed and available to the UI.
    if is_never_done:
        baseline_km: Optional[int] = cfg.vehicle.initial_km if interval_km else None
        baseline_date: Optional[str] = cfg.vehicle.initial_date if interval_months else None
    else:
        baseline_km = last_done_km
        baseline_date = last_done_date

    next_due_km: Optional[int] = None
    next_due_date: Optional[date] = None
    km_remaining: Optional[int] = None
    days_remaining: Optional[int] = None

    if baseline_km is not None and interval_km is not None:
        next_due_km = baseline_km + interval_km
        km_remaining = next_due_km - current_km

    if baseline_date is not None and interval_months is not None:
        next_due_date = _resolve_next_due_date(baseline_date, interval_months)
        days_remaining = (next_due_date - current_date).days

    # Determine status — overdue takes priority over due_soon
    km_overdue = next_due_km is not None and current_km >= next_due_km
    date_overdue = next_due_date is not None and current_date >= next_due_date

    if km_overdue or date_overdue:
        status = TaskStatus.overdue
    elif is_never_done:
        status = TaskStatus.never_done
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
    """Load all tasks from Airtable and compute their status.

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
        tasks = get_all_task_dicts(cfg.airtable.tasks_table)
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


def mark_task_done(table_name: str, task_id: str, done_km: int, done_date: date) -> None:
    """Update a task's last_done_km and last_done_date fields in Airtable.

    Args:
        table_name: Airtable table name for tasks.
        task_id: The task_id field value of the task to update.
        done_km: Odometer reading when the task was completed.
        done_date: Calendar date when the task was completed.

    Raises:
        ValueError: If no task with the given task_id is found.
        Exception: If the Airtable write fails.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:mark_task_done task_id={task_id} done_km={done_km} done_date={done_date}")
    try:
        update_task_done(table_name, task_id, done_km, done_date)
        logger.info(
            f"END:mark_task_done task_id={task_id} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:mark_task_done task_id={task_id} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


def get_one_task_result(
    table_name: str,
    task_id: str,
    current_km: int,
    current_date: date,
    cfg,
) -> Optional[TaskResult]:
    """Fetch a single task from Airtable and compute its status.

    Args:
        table_name: Airtable table name for tasks.
        task_id: The task_id field value.
        current_km: Current estimated odometer reading in km.
        current_date: Today's date.
        cfg: AppConfig instance.

    Returns:
        TaskResult if found, or None if no matching task exists.
    """
    task = get_task_dict(table_name, task_id)
    if task is None:
        return None
    return compute_status(task, current_km, current_date, cfg)
