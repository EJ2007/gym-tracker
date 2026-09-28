import streamlit as st


st.set_page_config(page_title="Gym Trackers", page_icon=":material/fitness_center:", layout="centered")

st.title("Gym Tracker")
st.write("Log your workouts and build this app one feature at a time.")

if "workout_plan" not in st.session_state:
    st.session_state.workout_plan = []

if "saved_workout_plans" not in st.session_state:
    st.session_state.saved_workout_plans = []

if "show_plan_name_input" not in st.session_state:
    st.session_state.show_plan_name_input = False

st.header("Build a workout plan")

with st.form("exercise_form", clear_on_submit=True):
    exercise = st.text_input("Exercise", placeholder="Bench press")
    sets = st.number_input("Sets", min_value=1, max_value=20, value=3)
    reps = st.number_input("Reps", min_value=1, max_value=100, value=10)
    weight = st.number_input("Weight", min_value=0.0, value=0.0, step=2.5)

    add_exercise = st.form_submit_button("Add exercise")

if add_exercise:
    if exercise:
        st.session_state.workout_plan.append(
            {
                "Exercise": exercise,
                "Sets": sets,
                "Reps": reps,
                "Weight": weight,
            }
        )
        st.success(f"Added: {sets} x {reps} {exercise} at {weight:g} lb")
    else:
        st.warning("Please enter an exercise name.")

st.subheader("Current workout plan")

if st.session_state.workout_plan:
    st.dataframe(st.session_state.workout_plan, use_container_width=True)

    save_column, clear_column = st.columns(2)

    with save_column:
        if st.button("Save workout plan"):
            st.session_state.show_plan_name_input = True

    with clear_column:
        if st.button("Clear workout plan"):
            st.success("Workout plan cleared.")
            st.session_state.workout_plan = []
            st.session_state.show_plan_name_input = False

    if st.session_state.show_plan_name_input:
        with st.form("plan_name_form"):
            plan_name = st.text_input("Workout plan name", placeholder="Push day")
            save_named_plan = st.form_submit_button("Save named plan")

        if save_named_plan:
            if plan_name:
                st.session_state.saved_workout_plans.append(
                    {
                        "Plan Name": plan_name,
                        "Exercises": st.session_state.workout_plan.copy(),
                    }
                )
                st.session_state.workout_plan = []
                st.session_state.show_plan_name_input = False
                st.success(f"Saved workout plan: {plan_name}")
                st.rerun()
            else:
                st.warning("Please enter a workout plan name.")
else:
    st.info("Add your first exercise to start building a plan.")

st.subheader("My plans")

if st.session_state.saved_workout_plans:
    for plan in st.session_state.saved_workout_plans:
        with st.expander(plan["Plan Name"]):
            st.dataframe(plan["Exercises"], use_container_width=True)
else:
    st.info("Saved workout plans will appear here.")
