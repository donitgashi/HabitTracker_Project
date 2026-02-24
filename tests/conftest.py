"""Shared pytest fixtures for final-phase tests."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

from habit_tracker.db import create_tables
from habit_tracker import auth
from habit_tracker.habit_manager import HabitManager


@pytest.fixture()
def temp_db() -> Iterator[str]:
    """Create a temporary SQLite DB file and point the app to it."""
    previous = os.environ.get("HABIT_DB_PATH")
    f = tempfile.NamedTemporaryFile(delete=False)
    f.close()
    db_path = f.name
    os.environ["HABIT_DB_PATH"] = db_path
    create_tables()
    try:
        yield db_path
    finally:
        if previous is None:
            os.environ.pop("HABIT_DB_PATH", None)
        else:
            os.environ["HABIT_DB_PATH"] = previous
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture()
def user_manager(temp_db: str) -> HabitManager:
    """Return a HabitManager for a fresh test user."""
    user = auth.register("testuser", "pw12345")
    assert user is not None
    return HabitManager(user.id)
