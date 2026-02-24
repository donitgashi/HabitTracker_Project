"""Authentication service.

Implements registration + login using bcrypt.
SQL queries are delegated to habit_tracker.db.
"""

from __future__ import annotations

from typing import Optional

import bcrypt

from .models.user import User
from . import db


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def register(username: str, password: str) -> Optional[User]:
    """Register a new user. Returns User or None if username exists."""
    existing = db.get_user_by_username(username)
    if existing is not None:
        return None
    user_id = db.insert_user(username, _hash_password(password))
    row = db.get_user_by_username(username)
    assert row is not None
    return User(id=row["id"], username=row["username"], password_hash=row["password_hash"])


def authenticate(username: str, password: str) -> Optional[User]:
    """Authenticate a user. Returns User on success, else None."""
    row = db.get_user_by_username(username)
    if row is None:
        return None
    stored = row["password_hash"].encode("utf-8")
    if bcrypt.checkpw(password.encode("utf-8"), stored):
        return User(id=row["id"], username=row["username"], password_hash=row["password_hash"])
    return None
