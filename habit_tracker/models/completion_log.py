"""Domain model for completion logs.

A completion is recorded whenever a user checks off a habit task.
The assignment requires storing the *date and time* of completion.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CompletionLog:
    id: Optional[int]
    habit_id: int
    completed_at: datetime.datetime
