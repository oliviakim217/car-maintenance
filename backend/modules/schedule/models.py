"""Pydantic models for the schedule module."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TaskStatus(str, Enum):
    """Computed status of a maintenance task."""

    ok = "ok"
    due_soon = "due_soon"
    overdue = "overdue"
    never_done = "never_done"


class TaskResult(BaseModel):
    """A maintenance task enriched with computed scheduling status.

    Combines the raw fields from tasks.json with derived fields that
    tell the user when the task is next due and how urgent it is.
    """

    # Raw fields from tasks.json
    id: str
    name: str
    category: str
    interval_km: Optional[int]
    interval_months: Optional[int]
    notes: str
    last_done_km: Optional[int]
    last_done_date: Optional[str]

    # Computed fields
    status: TaskStatus
    next_due_km: Optional[int] = None
    next_due_date: Optional[date] = None
    km_remaining: Optional[int] = None
    days_remaining: Optional[int] = None
