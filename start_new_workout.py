from copy import deepcopy
from datetime import datetime, timezone
import sqlite3
from uuid import uuid4

import streamlit as st

from database import (
    initialize_database,
    load_preferred_weight_unit,
    load_workout_plans,
    save_completed_workout,
)
from exercises import EXERCISES
from units import from_kg, to_kg, weight_label, weight_step


initialize_database()
preferred_weight_unit = load_preferred_weight_unit()

if "active_workout" not in st.session_state:
    st.session_state.active_workout = None

st.title("Start new workout")


def exercises_for_display(exercises, unit):
    return [
        {
            **exercise,
            "Weight": round(from_kg(exercise["Weight"], unit), 2),
        }
        for exercise in exercises
    ]


def sets_for_display(sets, unit):
    return [
        {
            **row,
            "Weight": round(from_kg(row["Weight"], unit), 2),
        }
        for row in sets
    ]


def sets_for_storage(sets, unit):
    return [
        {
            **row,
            "Weight": to_kg(row["Weight"], unit),
        }
        for row in sets
    ]

if "finished_workout_summary" in st.session_state:
    summary = st.session_state.finished_workout_summary
    st.success(f"Workout saved: {summary['name']}")
    st.caption(
        f"{summary['sets']} completed sets | {summary['minutes']:.1f} minutes"
    )

if st.session_state.active_workout is None:
    saved_plans = load_workout_plans()

    if not saved_plans:
        st.info("No saved plans yet.")
        st.page_link("workout_library.py", label="Workout Library", icon=":material/fitness_center:")
    else:
        plans_by_id = {plan["id"]: plan for plan in saved_plans}
        selected_id = st.selectbox(
            "Workout plan",
            options=list(plans_by_id),
            format_func=lambda plan_id: (
                f"{plans_by_id[plan_id]['Plan Name']} (#{plan_id})"
            ),
            index=None,
            placeholder="Select a plan",
        )

        if selected_id is not None:
            selected_plan = plans_by_id[selected_id]
            plan_display_unit = st.segmented_control(
                "Show plan weights in",
                ["kg", "lb"],
                default=preferred_weight_unit,
                key=f"start_plan_display_unit_{selected_id}",
            )
            st.dataframe(
                exercises_for_display(selected_plan["Exercises"], plan_display_unit),
                hide_index=True,
                width="stretch",
                column_config={
                    "Weight": st.column_config.NumberColumn(
                        weight_label(plan_display_unit)
                    )
                },
            )

            if st.button(
                "Start workout",
                icon=":material/play_arrow:",
                type="primary",
                disabled=not selected_plan["Exercises"],
            ):
                # Copy the exercises so workout edits won't change the saved plan.
                st.session_state.active_workout = {
                    "session_key": str(uuid4()),
                    "plan_id": selected_id,
                    "Plan Name": selected_plan["Plan Name"],
                    "Exercises": deepcopy(selected_plan["Exercises"]),
                    "started_at": datetime.now(timezone.utc),
                }
                st.session_state.pop("finished_workout_summary", None)
                st.rerun()
else:
    workout = st.session_state.active_workout
    if "session_key" not in workout:
        workout["session_key"] = str(uuid4())
    st.subheader(workout["Plan Name"])
    st.caption("*Click Apply changes before switching pages to save your workout edits.")
    workout_display_unit = st.segmented_control(
        "Show workout weights in",
        ["kg", "lb"],
        default=preferred_weight_unit,
        key=f"active_workout_display_unit_{workout['session_key']}",
    )

    # Expand each planned exercise into separate sets once per workout.
    if "Sets" not in workout:
        workout["Sets"] = [
            {
                "Exercise": exercise["Exercise"],
                "Set": set_number,
                "Reps": exercise["Reps"],
                "Weight": exercise["Weight"],
                "Completed": False,
            }
            for exercise in workout["Exercises"]
            for set_number in range(1, exercise["Sets"] + 1)
        ]
        workout["editor_version"] = 0

    # Keep exercise names outside the tables, but retain them in the saved rows.
    exercise_groups = {}
    for row in workout["Sets"]:
        exercise_groups.setdefault(row["Exercise"], []).append(
            {column: value for column, value in row.items() if column != "Exercise"}
        )

    with st.form("workout_sets_form"):
        edited_sets = []
        exercise_to_delete = None
        for index, (exercise_name, sets) in enumerate(exercise_groups.items()):
            st.subheader(exercise_name)
            editor_key = f"workout_sets_{workout['started_at'].isoformat()}_{workout['editor_version']}_{workout_display_unit}_{index}"
            edited_rows = st.data_editor(
                sets_for_display(sets, workout_display_unit),
                key=editor_key,
                hide_index=True,
                width="stretch",
                num_rows="dynamic",
                column_config={
                    "Set": st.column_config.NumberColumn(
                        "Set", min_value=1, step=1, default=1, required=True
                    ),
                    "Reps": st.column_config.NumberColumn(
                        "Reps", min_value=0, step=1, default=10, required=True
                    ),
                    "Weight": st.column_config.NumberColumn(
                        weight_label(workout_display_unit),
                        min_value=0.0,
                        step=weight_step(workout_display_unit),
                        default=0.0,
                        required=True,
                    ),
                    "Completed": st.column_config.CheckboxColumn("Completed", default=False),
                },
            )
            edited_sets.extend(
                {"Exercise": exercise_name, **row}
                for row in sets_for_storage(edited_rows, workout_display_unit)
            )
            if st.form_submit_button(
                "Delete exercise", icon=":material/delete:", key=f"{editor_key}_delete"
            ):
                exercise_to_delete = exercise_name
        with st.container(horizontal_alignment="right"):
            apply_changes = st.form_submit_button("Apply changes", icon=":material/check:")

        st.subheader("Add exercise")
        new_exercise = st.selectbox(
            "Exercise",
            EXERCISES,
            index=None,
            accept_new_options=True,
            filter_mode="contains",
            key=f"new_workout_exercise_{workout['editor_version']}",
        )
        add_exercise = st.form_submit_button("Add exercise", icon=":material/add:")
        with st.container(horizontal_alignment="right"):
            finish_workout = st.form_submit_button(
                "Finish workout", icon=":material/check_circle:", type="primary"
            )

    if finish_workout:
        finished_at = datetime.now(timezone.utc)
        try:
            save_completed_workout(workout, edited_sets, finished_at)
        except ValueError as error:
            st.warning(str(error))
        except sqlite3.Error:
            st.error("Couldn't save the workout. Your workout is still open; please try again.")
        else:
            st.session_state.finished_workout_summary = {
                "name": workout["Plan Name"],
                "sets": sum(bool(row.get("Completed")) for row in edited_sets),
                "minutes": max(0, (finished_at - workout["started_at"]).total_seconds()) / 60,
            }
            st.session_state.active_workout = None
            st.rerun()

    if exercise_to_delete is not None:
        workout["Sets"] = [
            row for row in edited_sets if row["Exercise"] != exercise_to_delete
        ]
        workout["editor_version"] += 1
        st.rerun()

    if add_exercise:
        if not new_exercise or not new_exercise.strip():
            st.warning("Please enter an exercise name.")
        else:
            name = new_exercise.strip()
            existing_names = {row["Exercise"].casefold() for row in edited_sets}
            if name.casefold() in existing_names:
                st.warning("This exercise is already in the workout. Add sets in its table.")
            else:
                workout["Sets"] = edited_sets + [{
                    "Exercise": name,
                    "Set": 1,
                    "Reps": 10,
                    "Weight": 0.0,
                    "Completed": False,
                }]
                workout["editor_version"] += 1
                st.rerun()

    if apply_changes:
        if not edited_sets:
            st.warning("Keep at least one set, or cancel the workout.")
        elif any(not (row.get("Exercise") or "").strip() for row in edited_sets):
            st.warning("Enter an exercise name for every set.")
        else:
            workout["Sets"] = edited_sets
            # A new editor key prevents old row edits being applied twice.
            workout["editor_version"] += 1
            st.rerun()

    if st.button("Cancel workout", icon=":material/close:"):
        st.session_state.active_workout = None
        st.rerun()
