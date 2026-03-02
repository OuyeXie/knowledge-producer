from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")


def now_pacific() -> datetime:
    """Return the current time in Pacific Time."""
    return datetime.now(PACIFIC)


def today_pacific() -> date:
    """Return today's date in Pacific Time."""
    return now_pacific().date()


def to_pacific(dt: datetime) -> datetime:
    """Convert a datetime to Pacific Time, assuming naive values are UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PACIFIC)
