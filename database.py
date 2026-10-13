import sqlite3
import math
from pathlib import Path


DB_PATH = Path(__file__).with_name("workouts.db")
WEIGHT_UNIT_PREFERENCE_KEY = "preferred_weight_unit"
VALID_WEIGHT_UNITS = {"kg", "lb"}


def initialize_database():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS workout_plans (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS plan_exercises (
                    id INTEGER PRIMARY KEY,
                    plan_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    exercise TEXT NOT NULL,
                    sets INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    FOREIGN KEY (plan_id)
                        REFERENCES workout_plans(id)
                        ON DELETE CASCADE
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS completed_workouts (
                    id INTEGER PRIMARY KEY,
                    session_key TEXT NOT NULL UNIQUE,
                    plan_name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    duration_seconds REAL NOT NULL CHECK (duration_seconds >= 0),
                    weight_unit TEXT NOT NULL DEFAULT 'kg'
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS completed_sets (
                    id INTEGER PRIMARY KEY,
                    workout_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    exercise TEXT NOT NULL,
                    set_number INTEGER NOT NULL CHECK (set_number >= 1),
                    reps INTEGER NOT NULL CHECK (reps >= 0),
                    weight REAL NOT NULL CHECK (weight >= 0),
                    FOREIGN KEY (workout_id)
                        REFERENCES completed_workouts(id) ON DELETE CASCADE
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS app_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            migrated = connection.execute(
                "SELECT value FROM app_metadata WHERE key = 'weights_migrated_to_kg'"
            ).fetchone()

            if migrated is None:
                connection.execute(
                    "UPDATE plan_exercises SET weight = weight / 2.20462"
                )
                connection.execute(
                    "UPDATE completed_sets SET weight = weight / 2.20462"
                )
                connection.execute(
                    "UPDATE completed_workouts SET weight_unit = 'kg'"
                )
                connection.execute(
                    """
                    INSERT INTO app_metadata (key, value)
                    VALUES ('weights_migrated_to_kg', 'true')
                    """
                )
    finally:
        connection.close()


def save_workout_plan(plan_name, exercises):
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.execute(
                "INSERT INTO workout_plans (name) VALUES (?)",
                (plan_name,),
            )

            plan_id = cursor.lastrowid

            for position, exercise in enumerate(exercises):
                connection.execute(
                    """
                    INSERT INTO plan_exercises
                        (plan_id, position, exercise, sets, reps, weight)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plan_id,
                        position,
                        exercise["Exercise"],
                        exercise["Sets"],
                        exercise["Reps"],
                        exercise["Weight"],
                    ),
                )

        return plan_id
    finally:
        connection.close()


def load_preferred_weight_unit():
    connection = sqlite3.connect(DB_PATH)

    try:
        row = connection.execute(
            "SELECT value FROM app_metadata WHERE key = ?",
            (WEIGHT_UNIT_PREFERENCE_KEY,),
        ).fetchone()
        if row is None or row[0] not in VALID_WEIGHT_UNITS:
            return "kg"
        return row[0]
    finally:
        connection.close()


def save_preferred_weight_unit(unit):
    if unit not in VALID_WEIGHT_UNITS:
        raise ValueError("Weight unit must be kg or lb.")

    connection = sqlite3.connect(DB_PATH)

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO app_metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (WEIGHT_UNIT_PREFERENCE_KEY, unit),
            )
    finally:
        connection.close()
        

def save_completed_workout(workout, sets, finished_at):
    completed_sets = [row for row in sets if row.get("Completed")]
    if not completed_sets:
        raise ValueError("Mark at least one set as Completed before finishing.")

    for row in completed_sets:
        if not (row.get("Exercise") or "").strip():
            raise ValueError("Each completed set needs an exercise name.")
        for field, minimum in (("Set", 1), ("Reps", 0), ("Weight", 0)):
            value = row.get(field)
            if (
                not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < minimum
                or (field != "Weight" and value != int(value))
            ):
                raise ValueError(f"Enter a valid {field.lower()} for each completed set.")

    duration = max(0, (finished_at - workout["started_at"]).total_seconds())
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            # Retrying the same workout must not create a second history entry.
            cursor = connection.execute(
                """
                INSERT INTO completed_workouts
                    (session_key, plan_name, started_at, finished_at, duration_seconds, weight_unit)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_key) DO NOTHING
                """,
                (workout["session_key"], workout["Plan Name"],
                 workout["started_at"].isoformat(), finished_at.isoformat(), duration, "kg"),
            )
            if cursor.rowcount == 0:
                return connection.execute(
                    "SELECT id FROM completed_workouts WHERE session_key = ?",
                    (workout["session_key"],),
                ).fetchone()[0]

            workout_id = cursor.lastrowid
            for position, row in enumerate(completed_sets):
                connection.execute(
                    """
                    INSERT INTO completed_sets
                        (workout_id, position, exercise, set_number, reps, weight)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (workout_id, position, row["Exercise"].strip(),
                     row["Set"], row["Reps"], row["Weight"]),
                )
        return workout_id
    finally:
        connection.close()


def load_workout_plans():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        plans = connection.execute(
            "SELECT id, name FROM workout_plans ORDER BY id"
        ).fetchall()

        saved_plans = []
        for plan in plans:
            exercises = connection.execute(
                """
                SELECT exercise, sets, reps, weight
                FROM plan_exercises
                WHERE plan_id = ?
                ORDER BY position, id
                """,
                (plan["id"],),
            ).fetchall()

            saved_plans.append(
                {
                    "id": plan["id"],
                    "Plan Name": plan["name"],
                    "Exercises": [
                        {
                            "Exercise": exercise["exercise"],
                            "Sets": exercise["sets"],
                            "Reps": exercise["reps"],
                            "Weight": exercise["weight"],
                        }
                        for exercise in exercises
                    ],
                }
            )

        return saved_plans
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
