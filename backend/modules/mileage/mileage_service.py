"""Mileage service module.

Manages reading and writing of odometer data stored in Airtable (Mileage table),
and provides an estimated current mileage based on configured daily averages.
"""

import logging
import time
from datetime import date
from typing import Dict

from backend.config.config_loader import get_config
from backend.services.airtable_service import add_mileage_entry, get_last_mileage_entry
from backend.utils.date_utils import estimate_km_driven

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_last_reading() -> Dict:
    """Return the most recent manual odometer entry from Airtable.

    Returns:
        Dict with keys 'date' (ISO string), 'km' (int), 'type' (str).

    Raises:
        ValueError: If the Mileage table has no entries.
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:get_last_reading")
    try:
        cfg = get_config()
        entry = get_last_mileage_entry(cfg.airtable.mileage_table)
        logger.info(f"END:get_last_reading duration_ms={int((time.monotonic() - start_ms) * 1000)}")
        return entry
    except Exception as exc:
        logger.error(
            f"ERROR:get_last_reading error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


def get_current_km() -> int:
    """Return the estimated current odometer reading.

    Takes the latest manual reading and adds the estimated km driven since
    that date, using the configured daily averages.

    Returns:
        Estimated current kilometres (int).
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:get_current_km")
    try:
        cfg = get_config()
        last = get_last_reading()

        last_km: int = int(last["km"])
        last_date = date.fromisoformat(last["date"])
        today = date.today()

        estimated = estimate_km_driven(
            start_date=last_date,
            end_date=today,
            weekday_km=cfg.mileage.weekday_km,
            weekend_km=cfg.mileage.weekend_km,
        )
        current_km = last_km + estimated
        logger.info(
            f"END:get_current_km last_km={last_km} estimated={estimated} "
            f"current_km={current_km} duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        return current_km
    except Exception as exc:
        logger.error(
            f"ERROR:get_current_km error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise


def add_manual_reading(km: int, reading_date: date) -> None:
    """Append a new manual odometer reading to Airtable.

    Args:
        km: The odometer value in kilometres.
        reading_date: The date of the reading.

    Raises:
        ValueError: If km is not a positive integer.
        Exception: If the Airtable write fails.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:add_manual_reading km={km} date={reading_date}")

    if km <= 0:
        raise ValueError(f"km must be a positive integer, got {km}")

    try:
        cfg = get_config()
        add_mileage_entry(cfg.airtable.mileage_table, km, reading_date)
        logger.info(
            f"END:add_manual_reading km={km} date={reading_date} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:add_manual_reading error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise
