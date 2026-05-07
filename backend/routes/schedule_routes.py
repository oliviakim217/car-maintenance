"""Schedule API routes.

Thin route handlers for maintenance task operations. All business logic
is delegated to schedule_service and related services.
"""

import logging
import re
import time
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.config.config_loader import get_config
from backend.modules.mileage.mileage_service import get_current_km
from backend.modules.schedule.models import TaskResult
from backend.modules.schedule.schedule_service import (
    get_all_tasks,
    get_one_task_result,
    mark_task_done,
)
from backend.services.airtable_service import append_maintenance_log
from backend.utils.auth import require_api_key
from backend.utils.limiter import limiter

logger = logging.getLogger(__name__)

_TASK_ID_RE = re.compile(r"^[a-z0-9_]{1,64}$")

router = APIRouter(dependencies=[Depends(require_api_key)])


# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------


class CompleteTaskBody(BaseModel):
    """Request body for marking a task as done."""

    model_config = ConfigDict(extra="forbid")

    done_km: int = Field(gt=0, le=999_999)
    done_date: str = Field(max_length=10)
    notes: str = Field(default="", max_length=500)

    @field_validator("done_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format: {v!r}. Expected YYYY-MM-DD.")
        return v


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("/api/schedule", response_model=List[TaskResult])
async def get_schedule() -> List[TaskResult]:
    """Return all maintenance tasks with their computed status.

    Current km is auto-calculated from the latest mileage entry plus
    estimated km driven since that reading.
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:get_schedule")
    try:
        cfg = get_config()
        current_km = get_current_km()
        today = date.today()
        return get_all_tasks(current_km, today, cfg)
    except Exception as exc:
        logger.error(f"ERROR:get_schedule error={exc} duration_ms={int((time.monotonic() - start_ms) * 1000)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve schedule")
    finally:
        logger.info(f"END:get_schedule duration_ms={int((time.monotonic() - start_ms) * 1000)}")


@router.post("/api/tasks/{task_id}/complete", response_model=TaskResult)
@limiter.limit(lambda: f"{get_config().rate_limiting.write_requests_per_minute}/minute")
async def complete_task(request: Request, task_id: str, body: CompleteTaskBody) -> TaskResult:
    """Mark a maintenance task as completed.

    Updates last_done fields in Airtable, appends a record to the
    Maintenance Log table, and returns the updated TaskResult.

    Args:
        task_id: The unique task identifier (task_id field value).
        body: JSON body with done_km, done_date (ISO string), and notes.
    """
    if not _TASK_ID_RE.match(task_id):
        raise HTTPException(status_code=422, detail="Invalid task_id format")

    done_date = date.fromisoformat(body.done_date)  # guaranteed valid by Pydantic

    start_ms = time.monotonic()
    logger.info(f"BEGIN:complete_task task_id={task_id} done_km={body.done_km} done_date={body.done_date}")
    try:
        cfg = get_config()
        mark_task_done(cfg.airtable.tasks_table, task_id, body.done_km, done_date)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"ERROR:complete_task task_id={task_id} error={exc} duration_ms={int((time.monotonic() - start_ms) * 1000)}")
        raise HTTPException(status_code=500, detail="Failed to mark task as done")
    finally:
        logger.info(f"END:complete_task task_id={task_id} duration_ms={int((time.monotonic() - start_ms) * 1000)}")

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
