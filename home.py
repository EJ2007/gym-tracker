from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import streamlit as st

from database import (
    initialize_database,
    load_preferred_weight_unit,
    load_weekly_progress,
)
from units import from_kg


initialize_database()

st.title("Home")

preferred_weight_unit = load_preferred_weight_unit()

st.header("Your weekly progress")

# Use Toronto's date even when the app server runs in another timezone.
toronto_timezone = ZoneInfo("America/Toronto")
today = datetime.now(toronto_timezone).date()

# weekday() is 0 on Monday and 6 on Sunday; subtract it to find Monday.
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=6)

# The query includes this Monday's midnight and excludes next Monday's midnight.
# Build both midnights locally before converting so daylight saving is respected.
week_start_local = datetime.combine(week_start, time.min, tzinfo=toronto_timezone)
week_end_local = datetime.combine(
    week_start + timedelta(days=7), time.min, tzinfo=toronto_timezone
)
week_start_utc = week_start_local.astimezone(timezone.utc)
week_end_utc = week_end_local.astimezone(timezone.utc)

# Read fresh totals whenever Home runs, including after finishing a workout.
weekly_progress = load_weekly_progress(week_start_utc, week_end_utc)

# Stored volume stays in kg; convert only the displayed value to the chosen unit.
display_volume = from_kg(weekly_progress["volume_kg"], preferred_weight_unit)
duration_hours = weekly_progress["duration_seconds"] / 3600

# Format volume with one decimal place and duration with two decimal places.
workouts, volume, duration = st.columns(3)
workouts.metric("Workouts", weekly_progress["workouts"], border=True)
volume.metric(f"Volume ({preferred_weight_unit})", f"{display_volume:,.1f}", border=True)
duration.metric("Duration (h)", f"{duration_hours:.2f}", border=True)

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
