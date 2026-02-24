"""Domain model for a habit.

This file intentionally contains **no SQL**. Persistence lives in habit_tracker.db.
Business logic lives in habit_tracker.habit_manager.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

from ..time_utils import Periodicity, normalize_periodicity


@dataclass
class Habit:
    id: Optional[int]
    user_id: int
    title: str
    description: str
    periodicity: str
    created_at: datetime.datetime
    last_completed_at: Optional[datetime.datetime] = None
    streak: int = 0

    @property
    def periodicity_norm(self) -> Periodicity:
        return normalize_periodicity(self.periodicity)
