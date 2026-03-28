"""Mileage service module.

Manages reading and writing of odometer data stored in data/mileage.json,
and provides an estimated current mileage based on configured daily averages.
"""

import json
import logging
import time
from datetime import date
from pathlib import Path
from typing import Dict, List

from backend.config.config_loader import get_config
from backend.utils.date_utils import estimate_km_driven

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MILEAGE_FILE = _PROJECT_ROOT / "data" / "mileage.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_mileage_data() -> Dict:
    """Read the raw mileage JSON file and return its contents.

    Returns:
        Dict containing 'entries' list.

    Raises:
        FileNotFoundError: If mileage.json does not exist.
        json.JSONDecodeError: If the file is malformed JSON.
    """
    with open(_MILEAGE_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_mileage_data(data: Dict) -> None:
    """Write mileage data back to disk.

    Args:
        data: The full mileage data dict to serialise.
    """
    with open(_MILEAGE_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_last_reading() -> Dict:
    """Return the most recent manual odometer entry.

    Returns:
        Dict with keys 'date', 'km', and 'type'.

    Raises:
        ValueError: If the mileage file has no entries.
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:get_last_reading")
    try:
        data = _read_mileage_data()
        entries: List[Dict] = data.get("entries", [])
        if not entries:
            raise ValueError("No mileage entries found in mileage.json")
        last = entries[-1]
        logger.info(f"END:get_last_reading duration_ms={int((time.monotonic() - start_ms) * 1000)}")
        return last
    except Exception as exc:
        logger.error(
            f"ERROR:get_last_reading error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise
    finally:
        pass


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

        last_km: int = last["km"]
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
    finally:
        pass


def add_manual_reading(km: int, reading_date: date) -> None:
    """Append a new manual odometer reading to mileage.json.

    Args:
        km: The odometer value in kilometres.
        reading_date: The date of the reading.

    Raises:
        ValueError: If km is not a positive integer.
        IOError: If the file cannot be read or written.
    """
    start_ms = time.monotonic()
    logger.info(f"BEGIN:add_manual_reading km={km} date={reading_date}")

    if km <= 0:
        raise ValueError(f"km must be a positive integer, got {km}")

    try:
        data = _read_mileage_data()
        entry = {"date": reading_date.isoformat(), "km": km, "type": "manual"}
        data.setdefault("entries", []).append(entry)
        _write_mileage_data(data)
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
    finally:
        pass
