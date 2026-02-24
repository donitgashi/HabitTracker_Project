# Habit Tracker Application (OOFPP Final Phase)

A command-line habit tracker written in Python with SQLite persistence.
It supports authentication, daily/weekly habits, completion tracking with date+time, streak calculations that respect habit periodicity, and a pure analytics module.

## Final-phase checklist coverage

This repository includes:
- Modular project structure (`habit_tracker/`, `tests/`)
- README + `.gitignore`
- Unit tests for CRUD and analytics functions
- 4 weeks of predefined demo habit data (`seed_demo.py`) used in tests
- Screenshots of functionality and unit-test results (see `screenshots/`)
- Basic comments/docstrings in code

## Features

- User registration and login (bcrypt)
- Create / edit / delete habits
- Daily and weekly periodicity
- Completion logging with timezone-aware timestamps
- Streak calculation based on consecutive periods (daily or weekly)
- Analytics:
  - list all habits
  - list titles
  - group habits by periodicity
  - filter habits by periodicity
  - longest streak overall
  - longest streak for a selected habit
- Demo dataset (5 habits + 4 weeks tracking data)

## Project structure

- `habit_tracker/db.py` → database access and SQL
- `habit_tracker/habit_manager.py` → business logic (CRUD, completions, streaks)
- `habit_tracker/analytics.py` → pure analytics functions
- `habit_tracker/seed_demo.py` → loads demo user + 5 habits + 4 weeks of data
- `habit_tracker/main.py` → CLI interface
- `tests/` → unit and integration tests
- `screenshots/` → evidence from functionality and tests

## Setup

### Prerequisites
- Python 3.7+ (recommended: latest Python 3)
- pip

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the app

```bash
python -m habit_tracker
```

The database file defaults to `habit_tracker.db` in the current directory.
You can override the path with an environment variable:

```bash
export HABIT_DB_PATH=/path/to/my.db
# Windows PowerShell: $env:HABIT_DB_PATH="C:\path\to\my.db"
```

## Load predefined demo data (5 habits + 4 weeks)

```bash
python -m habit_tracker.seed_demo
```

Login credentials:
- username: `demo`
- password: `demo`

## Streak rules (periodicity-aware)

A streak is the number of consecutive periods where the habit was completed at least once.

### Daily habits
- period = calendar day
- multiple completions on the same day do not increase streak
- missing a day resets the streak

### Weekly habits
- period = ISO week (year + week number)
- multiple completions in the same week do not increase streak
- missing a week resets the streak

## Run tests

```bash
python -m pytest -q
```

## Screenshots / Evidence

The screenshot are in the folder screenshots.
In there you will find the first flow, analytics output, seed demo summary, pytest results and bit more in details information what was tested.
