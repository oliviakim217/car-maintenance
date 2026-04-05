"""Excel service module.

Logs completed maintenance tasks to a local Excel (.xlsx) file using openpyxl.
The log file path is read from application config.
"""

import logging
import time
from datetime import date
from pathlib import Path
from typing import Optional

import openpyxl

logger = logging.getLogger(__name__)

_HEADER_ROW = ["Date", "Task Name", "Mileage (km)", "Notes"]

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_log_path(log_file: str) -> Path:
    """Resolve the Excel log file path relative to the project root.

    Args:
        log_file: Relative path string from config (e.g. 'data/maintenance_log.xlsx').

    Returns:
        Absolute Path to the log file.
    """
    return _PROJECT_ROOT / log_file


def _load_or_create_workbook(log_path: Path) -> openpyxl.Workbook:
    """Load an existing workbook or create a new one with a header row.

    Args:
        log_path: Absolute path to the .xlsx file.

    Returns:
        An openpyxl Workbook instance.
    """
    if log_path.exists():
        return openpyxl.load_workbook(log_path)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Maintenance Log"
    ws.append(_HEADER_ROW)
    logger.info(f"BEGIN:excel_service action=created_log_file path={log_path}")
    return wb


def log_completed_task(
    task_name: str,
    done_km: int,
    done_date: date,
    notes: str,
    log_file: Optional[str] = None,
) -> None:
    """Append a completed-task row to the Excel maintenance log.

    Creates the file and header row automatically if they do not exist.

    Args:
        task_name: Human-readable task name.
        done_km: Odometer reading at time of completion.
        done_date: Calendar date of completion.
        notes: Any additional notes to record.
        log_file: Relative path to the .xlsx file (uses 'data/maintenance_log.xlsx' if None).
    """
    start_ms = time.monotonic()
    logger.info(
        f"BEGIN:log_completed_task task={task_name!r} km={done_km} date={done_date}"
    )

    resolved_log_file = log_file or "data/maintenance_log.xlsx"
    log_path = _get_log_path(resolved_log_file)

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        wb = _load_or_create_workbook(log_path)
        ws = wb.active
        ws.append([done_date.isoformat(), task_name, done_km, notes])
        wb.save(log_path)

        logger.info(
            f"END:log_completed_task task={task_name!r} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:log_completed_task task={task_name!r} error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        # Do not re-raise — Excel logging is non-critical
