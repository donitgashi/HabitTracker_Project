Habit Tracker Application

A modular command-line Habit Tracker built with Python and SQLite.

The application allows users to create and manage habits, record completions, and analyze progress over time. 
It supports daily and weekly habits and calculates streaks based on the habit’s periodicity.

--------------------------------------------------
Main Features
--------------------------------------------------

- User registration and login
- Create, edit, and delete habits
- Mark habits as completed
- Support for daily and weekly habits
- Periodicity-aware streak calculations
- Analytics module for habit performance
- Predefined demo data (4 weeks) for testing and verification
- Unit tests for CRUD and analytics functionality

--------------------------------------------------
Project Structure
--------------------------------------------------

HabitTracker_Project/
├── habit_tracker/
│   ├── db.py
│   ├── habit_manager.py
│   ├── analytics.py
│   ├── seed_demo.py
│   ├── main.py
│   └── __main__.py
├── tests/
├── screenshots/
├── requirements.txt
├── .gitignore
└── README.txt

--------------------------------------------------
Technologies
--------------------------------------------------

- Python
- SQLite
- pytest

--------------------------------------------------
Setup
--------------------------------------------------

1) Clone the repository

git clone https://github.com/donitgashi/HabitTracker_Project.git
cd HabitTracker_Project

2) Create and activate a virtual environment (recommended)

Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

3) Install dependencies

python -m pip install -r requirements.txt

--------------------------------------------------
Run the Application
--------------------------------------------------

python -m habit_tracker

--------------------------------------------------
Load Demo Data (5 habits + 4 weeks)
--------------------------------------------------

python -m habit_tracker.seed_demo

Demo login:
- Username: demo
- Password: demo

--------------------------------------------------
Streak Logic 
--------------------------------------------------

Daily habits
- Streak increases only for consecutive days
- Multiple completions on the same day count once
- Missing a day resets the streak

Weekly habits
- Streak increases only for consecutive weeks
- Multiple completions in the same week count once
- Missing a week resets the streak

--------------------------------------------------
Run Tests
--------------------------------------------------

python -m pytest -v

If pytest is not installed:
pip install pytest

--------------------------------------------------
Test Coverage
--------------------------------------------------

The test suite includes:
- Habit creation
- Habit editing
- Habit deletion
- Analytics functions
- Daily and weekly streak calculations
- Verification using predefined 4-week time-series data

--------------------------------------------------
Screenshots / Evidence
--------------------------------------------------

The screenshots/ folder contains:
- application functionality screenshots
- analytics output screenshots
- unit test (pytest) result screenshots
--------------------------------------------------
Author
--------------------------------------------------

Donit Gashi

