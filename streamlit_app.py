import streamlit as st
import pandas as pd
import sys
from pathlib import Path

from db.db import database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
db = database()


st.set_page_config(
    layout="centered", page_title="Gym tings", page_icon="🏋️"
)

st.title("Welcome to Gym Tings! 🏋️‍♂️")

if not "valid_inputs_received" in st.session_state:
    st.session_state["valid_inputs_received"] = False

# --- Sidebar navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Gym Tracker", "Stats 1", "Stats 2", "Stats 3", "About"])

# --- Page content ---
if page == "Gym Tracker":
    st.title("Home Gym Tracker")
    df = pd.read_sql_query("SELECT * FROM gym_sessions", db.conn)
    st.dataframe(df)
elif page == "Stats 1":
    st.title("Stats 1")

elif page == "Stats 2":
    st.title("Stats 2")

elif page == "Stats 3":
    st.title("Stats 3")

elif page == "About":
    st.title("About")
