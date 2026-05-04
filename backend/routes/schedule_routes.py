"""Schedule API routes.

Thin route handlers for maintenance task operations. All business logic
is delegated to schedule_service and related services.
"""

import logging
from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config.config_loader import get_config
from backend.modules.mileage.mileage_service import get_current_km
from backend.modules.schedule.models import TaskResult
from backend.modules.schedule.schedule_service import (
    get_all_tasks,
    get_one_task_result,
    mark_task_done,
)
from backend.services.airtable_service import append_maintenance_log

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------


class CompleteTaskBody(BaseModel):
    """Request body for marking a task as done."""

    done_km: int
    done_date: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("/api/schedule", response_model=List[TaskResult])
async def get_schedule() -> List[TaskResult]:
    """Return all maintenance tasks with their computed status.

    Current km is auto-calculated from the latest mileage entry plus
    estimated km driven since that reading.
    """
    try:
        cfg = get_config()
        current_km = get_current_km()
        today = date.today()
        return get_all_tasks(current_km, today, cfg)
    except Exception as exc:
        logger.error(f"ERROR:get_schedule error={exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve schedule")


@router.post("/api/tasks/{task_id}/complete", response_model=TaskResult)
async def complete_task(task_id: str, body: CompleteTaskBody) -> TaskResult:
    """Mark a maintenance task as completed.

    Updates last_done fields in Airtable, appends a record to the
    Maintenance Log table, and returns the updated TaskResult.

    Args:
        task_id: The unique task identifier (task_id field value).
        body: JSON body with done_km, done_date (ISO string), and notes.
    """
    try:
        done_date = date.fromisoformat(body.done_date)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {body.done_date!r}")

    try:
        cfg = get_config()
        mark_task_done(cfg.airtable.tasks_table, task_id, body.done_km, done_date)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"ERROR:complete_task task_id={task_id} error={exc}")
        raise HTTPException(status_code=500, detail="Failed to mark task as done")

    # Append to Maintenance Log (non-critical — failures are swallowed here)
    try:
        cfg = get_config()
        result_before_log = get_one_task_result(
            cfg.airtable.tasks_table, task_id, body.done_km, done_date, cfg
        )
        task_name = result_before_log.name if result_before_log else task_id
        append_maintenance_log(
            table_name=cfg.airtable.maintenance_log_table,
            task_name=task_name,
            done_km=body.done_km,
            done_date=done_date,
            notes=body.notes,
        )
    except Exception as exc:
        logger.error(f"ERROR:complete_task maintenance_log error={exc}")

    # Return updated task with recomputed status
    try:
        cfg = get_config()
        current_km = get_current_km()
        result = get_one_task_result(
            cfg.airtable.tasks_table, task_id, current_km, date.today(), cfg
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"ERROR:complete_task recompute error={exc}")
        raise HTTPException(status_code=500, detail="Task updated but failed to return result")
