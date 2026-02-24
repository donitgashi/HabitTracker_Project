"""CRUD and demo-data tests for the final phase."""

from __future__ import annotations

import datetime as dt

from habit_tracker import auth, db
from habit_tracker.habit_manager import HabitManager
from habit_tracker.seed_demo import seed_demo_data


def test_create_edit_delete_habit_roundtrip(user_manager: HabitManager) -> None:
    mgr = user_manager
    created = mgr.create_habit(" Walk ", " 30 min ", "Daily")

    assert created.title == "Walk"
    assert created.description == "30 min"
    assert created.periodicity == "daily"
    assert created.streak == 0

    updated = mgr.edit_habit(
        created.id,
        title="Evening Walk",
        description="40 min outside",
        periodicity="Weekly",
    )
    assert updated.title == "Evening Walk"
    assert updated.description == "40 min outside"
    assert updated.periodicity == "weekly"
    assert updated.streak == 0
    assert updated.last_completed_at is None

    assert mgr.delete_habit(created.id) is True
    assert mgr.list_habits() == []


def test_edit_changing_periodicity_resets_streak_state(user_manager: HabitManager) -> None:
    mgr = user_manager
    habit = mgr.create_habit("Gym", "", "Daily")
    tz = dt.timezone.utc
    mgr.complete_habit(habit.id, completed_at=dt.datetime(2026, 1, 1, 8, 0, tzinfo=tz))
    mgr.complete_habit(habit.id, completed_at=dt.datetime(2026, 1, 2, 8, 0, tzinfo=tz))

    before = mgr.get_habit(habit.id)
    assert before.streak == 2
    assert before.last_completed_at is not None

    after = mgr.edit_habit(habit.id, periodicity="Weekly")
    assert after.periodicity == "weekly"
    assert after.streak == 0
    assert after.last_completed_at is None


def test_delete_habit_returns_false_for_unknown_id(user_manager: HabitManager) -> None:
    assert user_manager.delete_habit(99999) is False


def test_seed_demo_data_contains_5_habits_and_4_weeks_of_tracking(temp_db: str) -> None:
    seed_demo_data()

    demo_user = auth.authenticate("demo", "demo")
    assert demo_user is not None
    mgr = HabitManager(demo_user.id)
    habits = mgr.list_habits()

    assert len(habits) == 5
    daily = [h for h in habits if h.periodicity == "daily"]
    weekly = [h for h in habits if h.periodicity == "weekly"]
    assert len(daily) == 3
    assert len(weekly) == 2

    counts_by_title = {h.title: len(db.list_completions(h.id)) for h in habits}
    assert counts_by_title["Drink Water"] == 28  # 4 weeks of daily completions
    assert counts_by_title["Gym Workout"] == 4   # 4 weekly completions
    assert counts_by_title["Meal Prep"] == 4     # 4 weekly completions

    # Water was completed every day, so it should have a strong streak.
    water = next(h for h in habits if h.title == "Drink Water")
    assert water.streak >= 20
