"""Database access layer (SQLite).

All SQL statements live in this module. Other modules (e.g. HabitManager)
use the functions below instead of writing SQL directly.

The DB path can be overridden with the HABIT_DB_PATH environment variable.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
import datetime as _dt
from typing import Optional, List, Dict, Any

from .time_utils import normalize_periodicity

# ---------------------------
# Connection helpers
# ---------------------------

def get_db_path() -> str:
    """
    Return path to SQLite database file.

    - Override via HABIT_DB_PATH environment variable.
    - Default: ./habit_tracker.db (current working directory).
    """
    return os.environ.get("HABIT_DB_PATH", str(_dt_path_default()))


def _dt_path_default():
    # Local import to avoid heavy imports at module import time
    from pathlib import Path
    return Path.cwd() / "habit_tracker.db"


@contextmanager
def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()

    # Expand user (~) and make sure parent directory exists.
    from pathlib import Path
    p = Path(db_path).expanduser()

    # If HABIT_DB_PATH accidentally points to a directory, fail clearly.
    if p.exists() and p.is_dir():
        raise sqlite3.OperationalError(f"Database path points to a directory: {p}")

    parent = p.resolve().parent
    parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def _parse_iso_dt(value: Optional[str]) -> Optional[_dt.datetime]:
    if value is None:
        return None
    try:
        dt = _dt.datetime.fromisoformat(value)
    except Exception:
        return None
    # If old data is naive, treat as UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt


def _date_to_iso_dt(date_str: Optional[str], hour: int = 0) -> Optional[str]:
    """Convert YYYY-MM-DD to ISO datetime string (UTC) for migration."""
    if not date_str:
        return None
    try:
        d = _dt.date.fromisoformat(date_str)
        dt = _dt.datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=_dt.timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


# ---------------------------
# Schema / migration
# ---------------------------

def create_tables() -> None:
    """Create tables (and migrate from DATE columns if needed)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )

        # Detect whether 'habits' exists and whether it uses DATE columns
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='habits'")
        habits_exists = cur.fetchone() is not None

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completions'")
        completions_exists = cur.fetchone() is not None

        needs_migration = False
        if habits_exists:
            cur.execute("PRAGMA table_info(habits)")
            cols = {row[1]: (row[2] or "").upper() for row in cur.fetchall()}
            if cols.get("created_at") == "DATE" or cols.get("last_completed") == "DATE":
                needs_migration = True
        if completions_exists:
            cur.execute("PRAGMA table_info(completions)")
            cols = {row[1]: (row[2] or "").upper() for row in cur.fetchall()}
            if cols.get("completed_at") == "DATE":
                needs_migration = True

        if needs_migration:
            _migrate_date_to_datetime(conn)

        # Create/ensure the final schema (TEXT ISO timestamps)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                periodicity TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_completed_at TEXT,
                streak INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
                completed_at TEXT NOT NULL
            )
            """
        )

        conn.commit()


def _migrate_date_to_datetime(conn: sqlite3.Connection) -> None:
    """Migrate from the initial DATE-based schema to ISO datetime TEXT."""
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    conn.commit()

    # Create new tables
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS habits_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            periodicity TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_completed_at TEXT,
            streak INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS completions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_at TEXT NOT NULL
        )
        """
    )

    # Copy data from old tables if they exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='habits'")
    if cur.fetchone() is not None:
        for r in cur.execute("SELECT * FROM habits").fetchall():
            row = dict(r)
            created = _date_to_iso_dt(row.get("created_at"), hour=0) or row.get("created_at")
            # old column was 'last_completed'
            last = None
            if "last_completed" in row:
                last = _date_to_iso_dt(row.get("last_completed"), hour=12) or row.get("last_completed")
            if last is None and "last_completed_at" in row:
                last = row.get("last_completed_at")
            cur.execute(
                """
                INSERT INTO habits_new (id, user_id, title, description, periodicity, created_at, last_completed_at, streak)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("id"),
                    row.get("user_id"),
                    row.get("title"),
                    row.get("description"),
                    row.get("periodicity"),
                    created,
                    last,
                    int(row.get("streak") or 0),
                ),
            )

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completions'")
    if cur.fetchone() is not None:
        for r in cur.execute("SELECT * FROM completions").fetchall():
            row = dict(r)
            comp = _date_to_iso_dt(row.get("completed_at"), hour=12) or row.get("completed_at")
            cur.execute(
                "INSERT INTO completions_new (id, habit_id, completed_at) VALUES (?, ?, ?)",
                (row.get("id"), row.get("habit_id"), comp),
            )

    # Drop old tables and rename new ones
    cur.execute("DROP TABLE IF EXISTS completions;")
    cur.execute("DROP TABLE IF EXISTS habits;")
    cur.execute("ALTER TABLE habits_new RENAME TO habits;")
    cur.execute("ALTER TABLE completions_new RENAME TO completions;")
    conn.commit()

    cur.execute("PRAGMA foreign_keys = ON;")
    conn.commit()



# ---------------------------
# User queries
# ---------------------------

def insert_user(username: str, password_hash: str) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return int(cur.lastrowid)


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None


# ---------------------------
# Habit queries
# ---------------------------

def insert_habit(user_id: int, title: str, description: str, periodicity: str, created_at_iso: str) -> int:
    norm = normalize_periodicity(periodicity)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO habits (user_id, title, description, periodicity, created_at, last_completed_at, streak)
            VALUES (?, ?, ?, ?, ?, NULL, 0)
            """,
            (user_id, title, description, norm, created_at_iso),
        )
        conn.commit()
        return int(cur.lastrowid)


def update_habit(habit_id: int, user_id: int, *, title: str, description: str, periodicity: str,
                last_completed_at_iso: Optional[str], streak: int) -> None:
    norm = normalize_periodicity(periodicity)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE habits
            SET title = ?, description = ?, periodicity = ?, last_completed_at = ?, streak = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, description, norm, last_completed_at_iso, int(streak), int(habit_id), int(user_id)),
        )
        conn.commit()


def delete_habit(habit_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (int(habit_id), int(user_id)))
        conn.commit()
        return cur.rowcount > 0


def get_habit(habit_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM habits WHERE id = ?", (int(habit_id),))
        row = cur.fetchone()
        return dict(row) if row else None


def list_habits(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM habits WHERE user_id = ? ORDER BY created_at ASC", (int(user_id),))
        return [dict(r) for r in cur.fetchall()]


def delete_habits_for_user(user_id: int) -> None:
    """Delete all habits (and their completions via cascade) for a user."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM habits WHERE user_id = ?", (int(user_id),))
        conn.commit()


# ---------------------------
# Completion queries
# ---------------------------

def insert_completion(habit_id: int, completed_at_iso: str) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO completions (habit_id, completed_at) VALUES (?, ?)",
            (int(habit_id), completed_at_iso),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_last_completion(habit_id: int) -> Optional[str]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT completed_at FROM completions WHERE habit_id = ? ORDER BY completed_at DESC LIMIT 1",
            (int(habit_id),),
        )
        row = cur.fetchone()
        return row["completed_at"] if row else None


def list_completions(habit_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, habit_id, completed_at FROM completions WHERE habit_id = ? ORDER BY completed_at ASC",
            (int(habit_id),),
        )
        return [dict(r) for r in cur.fetchall()]


# ---------------------------
# Mapping helpers used by services
# ---------------------------

def habit_row_to_model(row: Dict[str, Any]):
    # imported lazily to avoid circular imports
    from .models.habit import Habit
    created = _parse_iso_dt(row.get("created_at")) or _dt.datetime.now(_dt.timezone.utc)
    last = _parse_iso_dt(row.get("last_completed_at"))
    return Habit(
        id=row.get("id"),
        user_id=row.get("user_id"),
        title=row.get("title") or "",
        description=row.get("description") or "",
        periodicity=row.get("periodicity") or "daily",
        created_at=created,
        last_completed_at=last,
        streak=int(row.get("streak") or 0),
    )