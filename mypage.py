import streamlit as st

from database import (
    initialize_database,
    load_preferred_weight_unit,
    save_preferred_weight_unit,
)


initialize_database()

st.title("My Page")
st.write("Personalized data, graphs and information.")

preferred_weight_unit = load_preferred_weight_unit()

st.header("Preferences")
selected_weight_unit = st.segmented_control(
    "Preferred weight unit",
    ["kg", "lb"],
    default=preferred_weight_unit,
)
if selected_weight_unit != preferred_weight_unit:
    save_preferred_weight_unit(selected_weight_unit)
    st.success(f"Weight unit preference saved as {selected_weight_unit}.")
