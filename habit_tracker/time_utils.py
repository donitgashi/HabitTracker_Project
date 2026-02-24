"""Time and streak utilities.

The assignment requires that we track the *date and time* of completions.
To keep streak calculation unambiguous, this module defines:

- how "periods" are interpreted for daily vs. weekly habits
- how to compare two completion timestamps
- how to detect whether a habit is due in the current period

All functions are pure (no I/O, no DB access).
"""

from __future__ import annotations

import datetime as _dt
from typing import Literal, Tuple, Union, Optional

Periodicity = Literal["daily", "weekly"]
PeriodKey = Union[str, Tuple[int, int]]  # daily: 'YYYY-MM-DD', weekly: (iso_year, iso_week)


def now_local() -> _dt.datetime:
    """Return a timezone-aware 'now' in the local timezone."""
    return _dt.datetime.now(_dt.timezone.utc).astimezone()


def normalize_periodicity(value: str) -> Periodicity:
    v = (value or "").strip().lower()
    if v in {"daily", "day"}:
        return "daily"
    if v in {"weekly", "week"}:
        return "weekly"
    raise ValueError(f"Unsupported periodicity: {value!r} (use Daily or Weekly)")


def period_key(dt: _dt.datetime, periodicity: Periodicity) -> PeriodKey:
    """Return the period key for a completion datetime.

    - Daily: local calendar day as ISO date string (YYYY-MM-DD)
    - Weekly: ISO week tuple (iso_year, iso_week) in local time
    """
    if dt.tzinfo is None:
        raise ValueError("dt must be timezone-aware")
    local = dt.astimezone()
    if periodicity == "daily":
        return local.date().isoformat()
    iso_year, iso_week, _iso_weekday = local.isocalendar()
    return (int(iso_year), int(iso_week))


def is_same_period(a: _dt.datetime, b: _dt.datetime, periodicity: Periodicity) -> bool:
    return period_key(a, periodicity) == period_key(b, periodicity)


def is_next_period(prev: _dt.datetime, curr: _dt.datetime, periodicity: Periodicity) -> bool:
    """True if 'curr' is in the *immediately following* period after 'prev'."""
    if prev.tzinfo is None or curr.tzinfo is None:
        raise ValueError("datetimes must be timezone-aware")

    prev_local = prev.astimezone()
    curr_local = curr.astimezone()

    if periodicity == "daily":
        return curr_local.date() == (prev_local.date() + _dt.timedelta(days=1))

    # weekly: consecutive ISO week
    py, pw, _ = prev_local.isocalendar()
    cy, cw, _ = curr_local.isocalendar()

    # compute next week from prev by adding 7 days
    next_local = prev_local + _dt.timedelta(days=7)
    ny, nw, _ = next_local.isocalendar()
    return (cy, cw) == (int(ny), int(nw))


def is_due(last_completed_at: Optional[_dt.datetime], now: _dt.datetime, periodicity: Periodicity) -> bool:
    """A habit is due if it has not been completed in the current period."""
    if last_completed_at is None:
        return True
    return period_key(last_completed_at, periodicity) != period_key(now, periodicity)
