"""Mileage API routes.

Thin route handlers for odometer reading operations. All business logic
is delegated to mileage_service.
"""

import logging
import time
from datetime import date
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.modules.mileage.mileage_service import (
    add_manual_reading,
    get_current_km,
    get_last_reading,
)
from backend.utils.auth import require_session
from backend.utils.limiter import limiter
from backend.utils.date_utils import estimate_km_driven
from backend.config.config_loader import get_config

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_session)])


# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------


class AddMileageBody(BaseModel):
    """Request body for adding a manual odometer reading."""

    model_config = ConfigDict(extra="forbid")

    km: int = Field(gt=0, le=999_999)
    date: str = Field(max_length=10)

    @field_validator("date")
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


@router.get("/api/mileage")
@limiter.limit(lambda: f"{get_config().rate_limiting.read_requests_per_minute}/minute")
async def get_mileage(request: Request) -> Dict:
    """Return the current estimated mileage and last manual reading.

    Returns:
        JSON with current_km, last_reading_km, last_reading_date, estimated_km.
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:get_mileage")
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
        logger.error(f"ERROR:get_mileage error={exc} duration_ms={int((time.monotonic() - start_ms) * 1000)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mileage data")
    finally:
        logger.info(f"END:get_mileage duration_ms={int((time.monotonic() - start_ms) * 1000)}")


@router.post("/api/mileage")
@limiter.limit(lambda: f"{get_config().rate_limiting.write_requests_per_minute}/minute")
async def post_mileage(request: Request, body: AddMileageBody) -> Dict:
    """Add a new manual odometer reading.

    Args:
        body: JSON body with 'km' (int) and 'date' (ISO date string).

    Returns:
        Updated mileage summary identical to GET /api/mileage.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:post_mileage km={body.km} date={body.date}")
    try:
        reading_date = date.fromisoformat(body.date)  # guaranteed valid by Pydantic
        add_manual_reading(km=body.km, reading_date=reading_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"ERROR:post_mileage error={exc} duration_ms={int((time.monotonic() - start_ms) * 1000)}")
        raise HTTPException(status_code=500, detail="Failed to save mileage reading")
    finally:
        logger.info(f"END:post_mileage duration_ms={int((time.monotonic() - start_ms) * 1000)}")

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
