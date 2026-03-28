"""Date utility functions for mileage estimation."""

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


def count_weekdays(start: date, end: date) -> int:
    """Count the number of weekdays (Mon–Fri) between start and end, inclusive.

    Args:
        start: The first date of the range.
        end: The last date of the range (inclusive).

    Returns:
        Number of weekday days in the range. Returns 0 if end < start.
    """
    if end < start:
        return 0

    total_days = (end - start).days + 1
    full_weeks, remainder = divmod(total_days, 7)
    weekdays = full_weeks * 5

    start_dow = start.weekday()  # 0=Mon … 6=Sun
    for offset in range(remainder):
        if (start_dow + offset) % 7 < 5:
            weekdays += 1

    return weekdays


def count_weekend_days(start: date, end: date) -> int:
    """Count the number of weekend days (Sat–Sun) between start and end, inclusive.

    Args:
        start: The first date of the range.
        end: The last date of the range (inclusive).

    Returns:
        Number of weekend days in the range. Returns 0 if end < start.
    """
    if end < start:
        return 0

    total_days = (end - start).days + 1
    return total_days - count_weekdays(start, end)


def estimate_km_driven(
    start_date: date,
    end_date: date,
    weekday_km: int,
    weekend_km: int,
) -> int:
    """Estimate kilometres driven between two dates based on daily averages.

    Args:
        start_date: The date of the last known odometer reading (exclusive —
            km on that day are already counted in the reading).
        end_date: The current date (inclusive).
        weekday_km: Estimated kilometres driven per weekday.
        weekend_km: Estimated kilometres driven per weekend day.

    Returns:
        Estimated total kilometres driven since start_date (exclusive).
        Returns 0 if end_date <= start_date.
    """
    if end_date <= start_date:
        return 0

    # The day after start_date is the first day to count
    count_start = start_date + timedelta(days=1)

    weekdays = count_weekdays(count_start, end_date)
    weekend_days = count_weekend_days(count_start, end_date)

    return (weekdays * weekday_km) + (weekend_days * weekend_km)
