import os
import tempfile
import datetime as dt

from habit_tracker.db import create_tables
from habit_tracker import auth
from habit_tracker.habit_manager import HabitManager
from habit_tracker.analytics import group_by_periodicity, longest_streak_overall, habits_with_periodicity

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


def test_analytics_group_and_longest_streak() -> None:
    user = auth.register("dave", "pw")
    assert user
    mgr = HabitManager(user.id)

    h1 = mgr.create_habit("Water", "", "Daily")
    h2 = mgr.create_habit("Gym", "", "Weekly")

    tz = dt.timezone.utc
    mgr.complete_habit(h1.id, completed_at=dt.datetime(2026, 1, 1, 10, 0, tzinfo=tz))
    mgr.complete_habit(h1.id, completed_at=dt.datetime(2026, 1, 2, 10, 0, tzinfo=tz))
    mgr.complete_habit(h2.id, completed_at=dt.datetime(2026, 1, 5, 10, 0, tzinfo=tz))

    habits = mgr.list_habits()
    groups = group_by_periodicity(habits)
    assert set(groups.keys()) == {"daily", "weekly"}

    daily = habits_with_periodicity(habits, "daily")
    assert len(daily) == 1 and daily[0].title == "Water"

    top, streak = longest_streak_overall(habits)
    assert top is not None
    assert top.title == "Water"
    assert streak == 2
