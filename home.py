from datetime import date, timedelta

import streamlit as st

from database import (
    initialize_database,
    load_preferred_weight_unit,
)


initialize_database()

st.title("Home")

preferred_weight_unit = load_preferred_weight_unit()

st.header("Your weekly progress")

# These totals will be connected to completed workout logs later.
workouts, volume, duration = st.columns(3)
workouts.metric("Workouts", 0, border=True)
volume.metric(f"Volume ({preferred_weight_unit})", 0, border=True)
duration.metric("Duration (h)", 0, border=True)

today = date.today()
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=6)

st.subheader("This week")
st.caption(f"{week_start:%b %d, %Y} - {week_end:%b %d, %Y}")

calendar = {}
for offset in range(7):
    day = week_start + timedelta(days=offset)
    if day < today:
        daily_message = "\n\n Past workouts"
    
    elif day == today:
        daily_message = "\n\n What's for today?"
        
    else:
        daily_message = "\n\n Future workouts"
    
    calendar[day.strftime("%a")] = f"**{day.day}**" + (daily_message
    )

st.table([calendar], hide_index=True)
