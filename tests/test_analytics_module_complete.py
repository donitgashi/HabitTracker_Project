"""Pure-function tests for every analytics function."""

from __future__ import annotations

import datetime as dt

import pytest

from habit_tracker.analytics import (
    all_habits,
    group_by_periodicity,
    habits_with_periodicity,
    list_titles,
    longest_streak_for_habit,
    longest_streak_overall,
)
from habit_tracker.models.habit import Habit


TZ = dt.timezone.utc


def _habit(
    habit_id: int,
    title: str,
    periodicity: str,
    streak: int,
) -> Habit:
    now = dt.datetime(2026, 1, 1, 12, 0, tzinfo=TZ)
    return Habit(
        id=habit_id,
        user_id=1,
        title=title,
        description="",
        periodicity=periodicity,
        created_at=now,
        last_completed_at=None,
        streak=streak,
    )


def test_all_habits_returns_list_copy() -> None:
    habits = [_habit(1, "Water", "daily", 3), _habit(2, "Gym", "weekly", 2)]
    result = all_habits(iter(habits))
    assert isinstance(result, list)
    assert result == habits
    assert result is not habits


def test_list_titles_returns_titles_in_order() -> None:
    habits = [_habit(1, "Water", "daily", 3), _habit(2, "Gym", "weekly", 2)]
    assert list_titles(habits) == ["Water", "Gym"]


def test_habits_with_periodicity_filters_daily_and_weekly() -> None:
    habits = [_habit(1, "Water", "Daily", 3), _habit(2, "Gym", "Weekly", 2), _habit(3, "Read", "daily", 5)]
    assert [h.title for h in habits_with_periodicity(habits, "daily")] == ["Water", "Read"]
    assert [h.title for h in habits_with_periodicity(habits, "weekly")] == ["Gym"]


def test_habits_with_periodicity_rejects_invalid_value() -> None:
    habits = [_habit(1, "Water", "daily", 3)]
    with pytest.raises(ValueError):
        habits_with_periodicity(habits, "monthly")


def test_group_by_periodicity_groups_valid_and_ignores_invalid() -> None:
    habits = [
        _habit(1, "Water", "daily", 1),
        _habit(2, "Gym", "weekly", 2),
        _habit(3, "Broken", "monthly", 0),
    ]
    grouped = group_by_periodicity(habits)
    assert set(grouped.keys()) == {"daily", "weekly"}
    assert [h.title for h in grouped["daily"]] == ["Water"]
    assert [h.title for h in grouped["weekly"]] == ["Gym"]


def test_longest_streak_overall_returns_top_habit_and_value() -> None:
    habits = [_habit(1, "Water", "daily", 3), _habit(2, "Gym", "weekly", 7), _habit(3, "Read", "daily", 5)]
    habit, streak = longest_streak_overall(habits)
    assert habit is not None
    assert habit.title == "Gym"
    assert streak == 7


def test_longest_streak_overall_empty_input() -> None:
    habit, streak = longest_streak_overall([])
    assert habit is None
    assert streak == 0


def test_longest_streak_for_habit_returns_integer_streak() -> None:
    habit = _habit(1, "Stretch", "daily", 11)
    assert longest_streak_for_habit(habit) == 11
