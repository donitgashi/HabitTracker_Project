"""HabitManager service.

This module contains the application/business logic for habits and streaks.
It **does not** contain SQL; it uses habit_tracker.db for persistence.

Streak rules (as required by the assignment):
- A streak is the number of *consecutive periods* (daily or weekly) in which
  the habit was completed at least once.
- Completing a habit multiple times in the same period does NOT increase the streak.
- If one or more periods are missed, the streak resets to 1 on the next completion.
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional

from .models.habit import Habit
from .models.completion_log import CompletionLog
from .time_utils import now_local, normalize_periodicity, period_key, is_next_period, is_due
from . import db


class HabitManager:
    """High-level operations on a user's habits."""

    def __init__(self, user_id: int):
        self.user_id = int(user_id)

    # --------
    # CRUD
    # --------

    def create_habit(self, title: str, description: str, periodicity: str, *, created_at: Optional[_dt.datetime] = None) -> Habit:
        created_at = created_at or now_local()
        habit_id = db.insert_habit(self.user_id, title.strip(), description.strip(), periodicity, created_at.isoformat())
        return self.get_habit(habit_id)

    def list_habits(self) -> List[Habit]:
        rows = db.list_habits(self.user_id)
        return [db.habit_row_to_model(r) for r in rows]

    def get_habit(self, habit_id: int) -> Habit:
        row = db.get_habit(int(habit_id))
        if not row or int(row.get("user_id")) != self.user_id:
            raise ValueError("Habit not found or not owned by user")
        return db.habit_row_to_model(row)

    def edit_habit(
        self,
        habit_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        periodicity: Optional[str] = None,
    ) -> Habit:
        habit = self.get_habit(habit_id)
        if title is not None and title.strip() != "":
            habit.title = title.strip()
        if description is not None:
            habit.description = description.strip()
        if periodicity is not None and periodicity.strip() != "":
            old_p = normalize_periodicity(habit.periodicity)
            habit.periodicity = periodicity.strip()
            new_p = normalize_periodicity(habit.periodicity)
            if new_p != old_p:
                # Period meaning changed → reset current streak state
                habit.streak = 0
                habit.last_completed_at = None
        db.update_habit(
            habit_id=habit.id,
            user_id=self.user_id,
            title=habit.title,
            description=habit.description,
            periodicity=habit.periodicity,
            last_completed_at_iso=habit.last_completed_at.isoformat() if habit.last_completed_at else None,
            streak=habit.streak,
        )
        return self.get_habit(habit_id)

    def delete_habit(self, habit_id: int) -> bool:
        return db.delete_habit(int(habit_id), self.user_id)

    # --------
    # Completion + streak logic
    # --------

    def complete_habit(self, habit_id: int, *, completed_at: Optional[_dt.datetime] = None) -> CompletionLog:
        """Mark a habit complete at a given time (defaults to now, local time)."""
        habit = self.get_habit(habit_id)
        completed_at = completed_at or now_local()
        if completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware")

        periodicity = normalize_periodicity(habit.periodicity)

        # Determine last completion from habit record (fast path). If missing, also check table.
        last_dt = habit.last_completed_at
        if last_dt is None:
            last_iso = db.get_last_completion(habit.id)  # might exist if record got out of sync
            if last_iso:
                last_dt = _dt.datetime.fromisoformat(last_iso)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=_dt.timezone.utc)

        # Update streak according to period keys
        if last_dt is None:
            new_streak = 1
        else:
            if period_key(last_dt, periodicity) == period_key(completed_at, periodicity):
                new_streak = habit.streak  # already completed this period
            elif is_next_period(last_dt, completed_at, periodicity):
                new_streak = habit.streak + 1
            else:
                new_streak = 1

        # Persist completion log (always record the event)
        completion_id = db.insert_completion(habit.id, completed_at.isoformat())

        # Persist habit state
        habit.last_completed_at = completed_at
        habit.streak = int(new_streak)

        db.update_habit(
            habit_id=habit.id,
            user_id=self.user_id,
            title=habit.title,
            description=habit.description,
            periodicity=habit.periodicity,
            last_completed_at_iso=habit.last_completed_at.isoformat(),
            streak=habit.streak,
        )

        return CompletionLog(id=completion_id, habit_id=habit.id, completed_at=completed_at)

    def due_habits(self, *, now: Optional[_dt.datetime] = None) -> List[Habit]:
        now = now or now_local()
        due: List[Habit] = []
        for habit in self.list_habits():
            p = normalize_periodicity(habit.periodicity)
            if is_due(habit.last_completed_at, now, p):
                due.append(habit)
        return due
