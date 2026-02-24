"""Analytics utilities (functional programming).

All functions in this module are **pure**:
- they take data as input (lists/iterables of Habit objects)
- they return computed results
- they do not modify program state and do not access the database

Minimal analytics required by the assignment:
- list all currently tracked habits
- list habits with the same periodicity
- longest run streak across all habits
- longest run streak for a given habit
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

from .models.habit import Habit
from .time_utils import normalize_periodicity


def all_habits(habits: Iterable[Habit]) -> List[Habit]:
    return list(habits)


def habits_with_periodicity(habits: Iterable[Habit], periodicity: str) -> List[Habit]:
    p = normalize_periodicity(periodicity)
    return [h for h in habits if normalize_periodicity(h.periodicity) == p]


def group_by_periodicity(habits: Iterable[Habit]) -> Dict[str, List[Habit]]:
    groups: Dict[str, List[Habit]] = defaultdict(list)
    for habit in habits:
        try:
            p = normalize_periodicity(habit.periodicity)
            groups[p].append(habit)
        except ValueError:
            # ignore unknown periodicity values
            continue
    return dict(groups)


def longest_streak_overall(habits: Iterable[Habit]) -> Tuple[Optional[Habit], int]:
    max_habit: Optional[Habit] = None
    max_streak: int = 0
    for habit in habits:
        if habit.streak > max_streak:
            max_habit = habit
            max_streak = habit.streak
    return max_habit, max_streak


def longest_streak_for_habit(habit: Habit) -> int:
    return int(habit.streak)


def list_titles(habits: Iterable[Habit]) -> List[str]:
    return [habit.title for habit in habits]
