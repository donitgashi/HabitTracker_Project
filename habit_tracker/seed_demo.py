"""Demo data seeding.

The assignment requires:
- at least 5 predefined habits
- example tracking data for 4 weeks

This module provides a helper to (re)create a deterministic demo dataset in the
current database file.

Run it directly:
    python -m habit_tracker.seed_demo
"""

from __future__ import annotations

import datetime as _dt

from .db import create_tables, delete_habits_for_user
from .time_utils import now_local
from . import auth, db
from .habit_manager import HabitManager


def seed_demo_data() -> None:
    create_tables()

    # Ensure demo user exists
    demo = auth.register("demo", "demo")
    if demo is None:
        row = db.get_user_by_username("demo")
        assert row is not None
        from .models.user import User
        demo = User(id=row["id"], username=row["username"], password_hash=row["password_hash"])

    # Reset demo user's habits for a clean slate
    delete_habits_for_user(demo.id)

    mgr = HabitManager(demo.id)
    base_now = now_local()
    start = base_now - _dt.timedelta(days=28)

    # Predefined habits
    habits = [
        ("Drink Water", "At least 2 liters per day", "Daily"),
        ("Read 20 Pages", "Read a book for 20 pages", "Daily"),
        ("Morning Stretch", "10 minutes mobility", "Daily"),
        ("Gym Workout", "Full body workout", "Weekly"),
        ("Meal Prep", "Prepare meals for the week", "Weekly"),
    ]

    created_ids = []
    for title, desc, per in habits:
        h = mgr.create_habit(title, desc, per, created_at=start)
        created_ids.append(h.id)

    # Generate 4 weeks of example completions (1 per period)
    # Daily habits: 28-day window
    def day_ts(day_index: int, hour: int) -> _dt.datetime:
        dt = (start + _dt.timedelta(days=day_index)).replace(hour=hour, minute=0, second=0, microsecond=0)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=base_now.tzinfo)
        return dt

    # 1) Drink Water: completed every day
    water_id = created_ids[0]
    for i in range(28):
        mgr.complete_habit(water_id, completed_at=day_ts(i, 9))

    # 2) Read: completed most days, with a few misses
    read_id = created_ids[1]
    missed = {6, 13, 20}  # miss roughly once per week
    for i in range(28):
        if i in missed:
            continue
        mgr.complete_habit(read_id, completed_at=day_ts(i, 21))

    # 3) Stretch: started later (last 14 days)
    stretch_id = created_ids[2]
    for i in range(14, 28):
        mgr.complete_habit(stretch_id, completed_at=day_ts(i, 7))

    # Weekly habits: 4 weeks (use Mondays of each ISO week starting from start)
    def week_ts(week_offset: int, hour: int) -> _dt.datetime:
        dt = (start + _dt.timedelta(days=7 * week_offset)).replace(hour=hour, minute=0, second=0, microsecond=0)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=base_now.tzinfo)
        return dt

    gym_id = created_ids[3]
    meal_id = created_ids[4]
    for w in range(4):
        mgr.complete_habit(gym_id, completed_at=week_ts(w, 18))
        mgr.complete_habit(meal_id, completed_at=week_ts(w, 10))


if __name__ == "__main__":
    seed_demo_data()
    print("Demo data loaded. Log in as 'demo' with password 'demo'.")
