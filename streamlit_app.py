import streamlit as st
import plotly.express as px
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
    df = pd.read_sql_query("""
                           SELECT date AS Date, duration AS Duration, 
                           gym_name as Gym, category as Category 
                           FROM gym_sessions""", db.conn)
    st.dataframe(df)
elif page == "Stats 1":
    st.title("Stats 1")
    col1, col2, col3 = st.columns(3)

    with col1:
        category_grouped_df = pd.read_sql_query("""
                            SELECT category AS Category, COUNT(*) AS Session_Count 
                            FROM gym_sessions GROUP BY category
                            ORDER BY Session_Count DESC""", db.conn)
        st.dataframe(category_grouped_df)

        locaton_grouped_df = pd.read_sql_query("""
                            SELECT gym_name AS Gym, COUNT(*) AS Session_Count
                            FROM gym_sessions GROUP BY gym_name
                            ORDER BY Session_Count DESC""", db.conn)
        st.dataframe(locaton_grouped_df)

    with col2:
        month_grouped_by = pd.read_sql_query("""
                           SELECT strftime('%m-%Y', date) AS Year_Month, 
                            COUNT(*) AS Session_Count 
                           FROM gym_sessions GROUP BY Year_Month
                           ORDER BY Year_Month ASC""", db.conn)
        st.dataframe(month_grouped_by)
        st.line_chart(month_grouped_by.set_index('Year_Month'))

    with col3:
        locaton_grouped_df = pd.read_sql_query("""
                            SELECT gym_name AS Gym, COUNT(*) AS Session_Count
                            FROM gym_sessions GROUP BY gym_name
                            ORDER BY Session_Count DESC""", db.conn)
        st.dataframe(locaton_grouped_df)
        fig = px.pie(locaton_grouped_df, names="Gym", values="Session_Count", title="Pie Chart")
        st.plotly_chart(fig)


elif page == "Stats 2":
    st.title("Stats 2")

elif page == "Stats 3":
    st.title("Stats 3")

elif page == "About":
    st.title("About")
