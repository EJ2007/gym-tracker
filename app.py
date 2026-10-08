import streamlit as st

#Adds page title, icon in the browser tab at the top of the browser
st.set_page_config(
    page_title="Gym Tracker",
    page_icon=":material/fitness_center:",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Navigate through different sections and call the file for each section
page = st.navigation(
    [
        st.Page("home.py", title="Home", icon=":material/home:", default=True),
        st.Page(
            "workout_library.py",
            title="Workout Library",
            icon=":material/fitness_center:",
        ),
        st.Page("mypage.py", title="My Page", icon=":material/person:"),
    ],
    position="top",
)
# Keep the app name in the upper-left corner on every page.
st.html("""
    <style>
        /* Reserve the first 64px for the app title, including on small screens. */
        [data-testid="stHeader"] {
            top: 64px;
        }
        /* Extend the opaque header background across the entire title row. */
        [data-testid="stHeader"]::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 64px;
            background: inherit;
        }
        [data-testid="stSidebar"] {
            top: 64px;
            height: calc(100% - 64px);
        }
        [data-testid="stMainBlockContainer"] {
            padding-top: 10rem;
        }
        #gym-tracker-title {
            position: fixed;
            top: 14px;
            left: 20px;
            margin: 0;
            padding: 0;
            font-size: 24px;
            line-height: 32px;
            letter-spacing: 0;
            z-index: 999999;
            pointer-events: none;
        }
    </style>
    <h1 id="gym-tracker-title">Gym Tracker</h1>
""")
page.run()
