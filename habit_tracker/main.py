"""Command-line interface for the habit tracker."""

from __future__ import annotations

import getpass
from typing import Optional

from .db import create_tables
from . import auth
from .models.user import User
from .habit_manager import HabitManager
from .analytics import (
    group_by_periodicity,
    longest_streak_overall,
    longest_streak_for_habit,
    list_titles,
    habits_with_periodicity,
)
from .seed_demo import seed_demo_data


def prompt_int(prompt: str) -> Optional[int]:
    try:
        return int(input(prompt))
    except ValueError:
        print("Please enter a valid number.")
        return None


def login_flow() -> Optional[User]:
    while True:
        print("\nWelcome to the Habit Tracker!")
        print("1. Register")
        print("2. Log in")
        print("3. Exit")
        choice = input("Choose an option (1-3): ").strip()
        if choice == "1":
            username = input("Choose a username: ").strip()
            password = getpass.getpass("Choose a password: ")
            user = auth.register(username, password)
            if user:
                print("Registration successful! Please log in.")
            else:
                print("Username already taken. Please try again.")
        elif choice == "2":
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ")
            user = auth.authenticate(username, password)
            if user:
                print(f"Welcome, {user.username}!")
                return user
            print("Invalid credentials. Please try again.")
        elif choice == "3":
            print("Goodbye!")
            return None
        else:
            print("Invalid choice. Please select 1, 2 or 3.")


def show_analytics(manager: HabitManager) -> None:
    habits = manager.list_habits()
    if not habits:
        print("You have no habits yet. Create some to see analytics.")
        return

    while True:
        # Refresh the list in case habits were modified before entering analytics.
        habits = manager.list_habits()

        print("\nAnalytics Menu")
        print("1. List habit titles")
        print("2. Group habits by periodicity")
        print("3. List habits for a specific periodicity")
        print("4. Show habit with longest streak")
        print("5. Show longest streak for a selected habit")
        print("6. Back")
        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            for title in list_titles(habits):
                print(f"- {title}")
        elif choice == "2":
            groups = group_by_periodicity(habits)
            for period, group in groups.items():
                print(f"{period.capitalize()}: {', '.join(h.title for h in group)}")
        elif choice == "3":
            p = input("Periodicity (Daily/Weekly): ").strip()
            try:
                matching = habits_with_periodicity(habits, p)
            except ValueError:
                print("Please enter Daily or Weekly.")
                continue
            if not matching:
                print("No habits found for that periodicity.")
            else:
                for h in matching:
                    print(f"- {h.title} (streak {h.streak})")
        elif choice == "4":
            habit, streak = longest_streak_overall(habits)
            if habit:
                print(f"Longest streak: {habit.title} with {streak} consecutive periods.")
            else:
                print("No habits to evaluate.")
        elif choice == "5":
            for h in habits:
                print(f"ID: {h.id} - {h.title} ({h.periodicity}, current streak {h.streak})")
            habit_id = prompt_int("Enter habit ID: ")
            if habit_id is None:
                continue
            try:
                selected = manager.get_habit(habit_id)
            except ValueError:
                print("Habit not found or you do not own this habit.")
                continue
            streak = longest_streak_for_habit(selected)
            print(f"{selected.title}: longest/current streak = {streak} consecutive periods.")
        elif choice == "6":
            break
        else:
            print("Invalid option.")


def main_menu(user: User) -> None:
    manager = HabitManager(user.id)
    while True:
        print("\nMain Menu")
        print("1. List habits")
        print("2. Create a habit")
        print("3. Edit a habit")
        print("4. Delete a habit")
        print("5. Mark a habit as complete")
        print("6. View analytics")
        print("7. Load demo data (5 habits + 4 weeks)")
        print("8. Log out")
        choice = input("Choose an option (1-8): ").strip()

        if choice == "1":
            habits = manager.list_habits()
            if not habits:
                print("You have no habits yet.")
            else:
                print("Your habits:")
                for habit in habits:
                    last = habit.last_completed_at.isoformat() if habit.last_completed_at else "--"
                    created = habit.created_at.isoformat() if habit.created_at else "--"
                    print(
                        f"ID: {habit.id}, Title: {habit.title}, Period: {habit.periodicity}, "
                        f"Streak: {habit.streak}, Created: {created}, Last completed: {last}"
                    )

        elif choice == "2":
            title = input("Habit title: ").strip()
            description = input("Description (optional): ").strip()
            periodicity = input("Periodicity (Daily/Weekly): ").strip()
            try:
                manager.create_habit(title, description, periodicity)
                print("Habit created.")
            except ValueError as e:
                print(str(e))

        elif choice == "3":
            habit_id = prompt_int("Enter the ID of the habit to edit: ")
            if habit_id is None:
                continue
            title = input("New title (leave blank to keep unchanged): ").strip()
            description = input("New description (leave blank to keep unchanged): ").strip()
            periodicity = input("New periodicity (Daily/Weekly, leave blank to keep unchanged): ").strip()
            title = title or None
            description = description or None
            periodicity = periodicity or None
            try:
                updated = manager.edit_habit(habit_id, title=title, description=description, periodicity=periodicity)
                print(f"Habit updated: {updated.title}")
            except ValueError:
                print("Habit not found or you do not own this habit.")

        elif choice == "4":
            habit_id = prompt_int("Enter the ID of the habit to delete: ")
            if habit_id is None:
                continue
            if manager.delete_habit(habit_id):
                print("Habit deleted.")
            else:
                print("Habit not found or you do not own this habit.")

        elif choice == "5":
            due = manager.due_habits()
            if not due:
                print("No habits are due right now. Nice work!")
                continue
            print("Habits due:")
            for habit in due:
                print(f"ID: {habit.id} - {habit.title} (streak {habit.streak})")
            habit_id = prompt_int("Enter the ID of the habit you have completed: ")
            if habit_id is None:
                continue
            try:
                manager.complete_habit(habit_id)
                print("Completion recorded.")
            except ValueError:
                print("Habit not found or you do not own this habit.")

        elif choice == "6":
            show_analytics(manager)

        elif choice == "7":
            seed_demo_data()
            print("Demo data loaded. Log in as 'demo' with password 'demo'.")

        elif choice == "8":
            print("Logging out...\n")
            break

        else:
            print("Invalid option. Please select between 1 and 8.")


def main() -> None:
    create_tables()
    user = login_flow()
    if user:
        main_menu(user)


if __name__ == "__main__":
    main()
