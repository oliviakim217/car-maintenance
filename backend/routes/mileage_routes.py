"""Mileage API routes.

Thin route handlers for odometer reading operations. All business logic
is delegated to mileage_service.
"""

import logging
from datetime import date
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.modules.mileage.mileage_service import (
    add_manual_reading,
    get_current_km,
    get_last_reading,
)
from backend.utils.date_utils import estimate_km_driven
from backend.config.config_loader import get_config

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------


class AddMileageBody(BaseModel):
    """Request body for adding a manual odometer reading."""

    km: int
    date: str


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("/api/mileage")
async def get_mileage() -> Dict:
    """Return the current estimated mileage and last manual reading.

    Returns:
        JSON with current_km, last_reading_km, last_reading_date, estimated_km.
    """
    try:
        cfg = get_config()
        last = get_last_reading()
        last_km: int = last["km"]
        last_date = date.fromisoformat(last["date"])
        today = date.today()

        estimated_km = estimate_km_driven(
            start_date=last_date,
            end_date=today,
            weekday_km=cfg.mileage.weekday_km,
            weekend_km=cfg.mileage.weekend_km,
        )
        current_km = last_km + estimated_km

        return {
            "current_km": current_km,
            "last_reading_km": last_km,
            "last_reading_date": last["date"],
            "estimated_km": estimated_km,
        }
    except Exception as exc:
        logger.error(f"ERROR:get_mileage error={exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mileage data")


@router.post("/api/mileage")
async def post_mileage(body: AddMileageBody) -> Dict:
    """Add a new manual odometer reading.

    Args:
        body: JSON body with 'km' (int) and 'date' (ISO date string).

    Returns:
        Updated mileage summary identical to GET /api/mileage.
    """
    try:
        reading_date = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {body.date!r}")

    if body.km <= 0:
        raise HTTPException(status_code=422, detail="km must be a positive integer")

    try:
        add_manual_reading(km=body.km, reading_date=reading_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"ERROR:post_mileage error={exc}")
        raise HTTPException(status_code=500, detail="Failed to save mileage reading")

    # Return updated summary
    try:
        cfg = get_config()
        last = get_last_reading()
        last_km: int = last["km"]
        last_date = date.fromisoformat(last["date"])
        today = date.today()

        estimated_km = estimate_km_driven(
            start_date=last_date,
            end_date=today,
            weekday_km=cfg.mileage.weekday_km,
            weekend_km=cfg.mileage.weekend_km,
        )
        current_km = last_km + estimated_km

        return {
            "current_km": current_km,
            "last_reading_km": last_km,
            "last_reading_date": last["date"],
            "estimated_km": estimated_km,
        }
    except Exception as exc:
        logger.error(f"ERROR:post_mileage refresh error={exc}")
        raise HTTPException(status_code=500, detail="Reading saved but failed to return updated data")
