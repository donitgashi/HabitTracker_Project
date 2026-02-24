"""Integration tests for the habit tracker.

We use a temporary SQLite file for each test because ':memory:' creates a
fresh database *per connection*.
"""

import os
import tempfile
import datetime as dt

from habit_tracker.db import create_tables
from habit_tracker import auth
from habit_tracker.habit_manager import HabitManager

_DB_FILE = None


def setup_function() -> None:
    global _DB_FILE
    f = tempfile.NamedTemporaryFile(delete=False)
    f.close()
    _DB_FILE = f.name
    os.environ["HABIT_DB_PATH"] = _DB_FILE
    create_tables()


def teardown_function() -> None:
    global _DB_FILE
    if _DB_FILE and os.path.exists(_DB_FILE):
        os.remove(_DB_FILE)
    _DB_FILE = None


def test_register_and_login() -> None:
    user = auth.register("alice", "secret")
    assert user is not None
    logged = auth.authenticate("alice", "secret")
    assert logged is not None
    assert logged.username == "alice"


def test_daily_streak_same_day_not_incremented_and_miss_resets() -> None:
    user = auth.register("bob", "topsecret")
    assert user
    mgr = HabitManager(user.id)
    habit = mgr.create_habit("Drink water", "Hydrate daily", "Daily")

    tz = dt.timezone.utc
    day1 = dt.datetime(2026, 1, 1, 9, 0, tzinfo=tz)
    day1_late = dt.datetime(2026, 1, 1, 20, 0, tzinfo=tz)
    day2 = dt.datetime(2026, 1, 2, 10, 0, tzinfo=tz)
    day4 = dt.datetime(2026, 1, 4, 10, 0, tzinfo=tz)  # day3 missed

    mgr.complete_habit(habit.id, completed_at=day1)
    assert mgr.get_habit(habit.id).streak == 1

    # same day completion -> streak unchanged
    mgr.complete_habit(habit.id, completed_at=day1_late)
    assert mgr.get_habit(habit.id).streak == 1

    # next day -> streak increments
    mgr.complete_habit(habit.id, completed_at=day2)
    assert mgr.get_habit(habit.id).streak == 2

    # miss one day -> reset to 1
    mgr.complete_habit(habit.id, completed_at=day4)
    assert mgr.get_habit(habit.id).streak == 1


def test_weekly_streak_same_week_not_incremented_and_miss_resets() -> None:
    user = auth.register("carol", "pw")
    assert user
    mgr = HabitManager(user.id)
    habit = mgr.create_habit("Gym", "Workout", "Weekly")

    tz = dt.timezone.utc
    w1 = dt.datetime(2026, 1, 5, 12, 0, tzinfo=tz)   # Monday
    w1_again = dt.datetime(2026, 1, 6, 12, 0, tzinfo=tz)
    w2 = dt.datetime(2026, 1, 12, 12, 0, tzinfo=tz)  # next week
    w4 = dt.datetime(2026, 1, 26, 12, 0, tzinfo=tz)  # missed week in-between

    mgr.complete_habit(habit.id, completed_at=w1)
    assert mgr.get_habit(habit.id).streak == 1

    mgr.complete_habit(habit.id, completed_at=w1_again)
    assert mgr.get_habit(habit.id).streak == 1

    mgr.complete_habit(habit.id, completed_at=w2)
    assert mgr.get_habit(habit.id).streak == 2

    mgr.complete_habit(habit.id, completed_at=w4)
    assert mgr.get_habit(habit.id).streak == 1
