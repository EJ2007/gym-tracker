import streamlit as st

# Open session states when the page is loaded
if "workout_plan" not in st.session_state:
    st.session_state.workout_plan = []

if "saved_workout_plans" not in st.session_state:
    st.session_state.saved_workout_plans = []

if "active_plan_name" not in st.session_state:
    st.session_state.active_plan_name = None

if "show_workout_builder" not in st.session_state:
    st.session_state.show_workout_builder = st.session_state.active_plan_name is not None

# When 'Create new workout' button is clicked, this function is called.
@st.dialog("Name your workout plan")
def create_workout_plan():
    with st.form("new_plan_form"):
        plan_name = st.text_input("Workout plan name", placeholder="Push day")
        create = st.form_submit_button("Create", type="primary")

    if create:
        if plan_name.strip():
            st.session_state.active_plan_name = plan_name.strip()
            st.session_state.show_workout_builder = True
            st.rerun()
        else:
            st.warning("Please enter a workout plan name.")

# Add 'Create new workout plan' button
st.title("Your Library")
if st.button(
    "Create new workout plan",
    icon=":material/add:",
    disabled=st.session_state.active_plan_name is not None,
):
    create_workout_plan()

if st.session_state.active_plan_name is not None:
    if st.session_state.show_workout_builder:
        if st.button("Close workout builder", icon=":material/close:"):
            st.session_state.show_workout_builder = False
            st.rerun()
    else:
        if st.button("Resume workout plan", icon=":material/edit:"):
            st.session_state.show_workout_builder = True
            st.rerun()

# Page to add exercises following the 'Create new workout plan'
if st.session_state.active_plan_name is not None and st.session_state.show_workout_builder:
    st.header("Build a workout plan")
    st.text(st.session_state.active_plan_name)

    with st.form("exercise_form", clear_on_submit=True):
        exercise = st.text_input("Exercise", placeholder="Bench press")
        sets = st.number_input("Sets", min_value=1, max_value=20, value=3)
        reps = st.number_input("Reps", min_value=1, max_value=100, value=10)
        weight = st.number_input("Weight", min_value=0.0, value=0.0, step=2.5)

        add_exercise = st.form_submit_button("Add exercise")

    if add_exercise:
        if exercise.strip():
            st.session_state.workout_plan.append(
                {
                    "Exercise": exercise.strip(),
                    "Sets": sets,
                    "Reps": reps,
                    "Weight": weight,
                }
            )
            st.success(f"Added: {sets} x {reps} {exercise.strip()} at {weight:g} lb")
        else:
            st.warning("Please enter an exercise name.")
    
    # Section that shows the workout plan as user build on it.
    st.subheader("Current workout plan")
    
    
    if st.session_state.workout_plan:
        st.dataframe(st.session_state.workout_plan, width="stretch")

        save_column, clear_column = st.columns(2)
        # Option to save or clear the plan built so far.
        with save_column:
            if st.button("Save workout plan"):
                st.session_state.saved_workout_plans.append(
                    {
                        "Plan Name": st.session_state.active_plan_name,
                        "Exercises": st.session_state.workout_plan.copy(),
                    }
                )
                st.session_state.workout_plan = []
                st.session_state.active_plan_name = None
                st.session_state.show_workout_builder = False
                st.rerun()

        with clear_column:
            if st.button("Clear"):
                st.session_state.workout_plan = []
                st.rerun()
    else:
        st.info("Add your first exercise to start building a plan.")

st.subheader("My plans")

# If saved, show saved workout plans. If nothing added yet, print info message
if st.session_state.saved_workout_plans:
    for plan in st.session_state.saved_workout_plans:
        with st.expander(plan["Plan Name"]):
            st.dataframe(plan["Exercises"], width="stretch")
else:
    st.info("Saved workout plans will appear here.")
