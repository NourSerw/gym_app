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
db.create_tables()
db.from_csv_to_db()
# State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# Set page title and icon (favicon)
st.set_page_config(
    page_title="Gym Tings",
    page_icon="🏋️",  
    layout="wide",  
    initial_sidebar_state="expanded"  
)

st.title("Welcome to Gym Tings! 🏋️‍♂️")

if not "valid_inputs_received" in st.session_state:
    st.session_state["valid_inputs_received"] = False

# --- Sidebar navigation ---
st.sidebar.title("Menu")
if st.session_state.logged_in:
    st.sidebar.write(f"Logged in as: {st.session_state.user}")
    page = st.sidebar.radio("Go to", ["Gym Tracker", "Stats 1", "Stats 2", "Stats 3", "About", "Logout"])
else:
    page = st.sidebar.radio("Go to", ["Login", "About"])

# --- Page content ---
if page == "Login" and not st.session_state.logged_in:
    st.title("🔐 Login Page")
    st.write("This is the login page. Please enter your credentials to log in.")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if db.check_user_credentials(username, password):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

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

        max_vists_month_df = month_grouped_by[month_grouped_by['Session_Count'] == month_grouped_by['Session_Count'].max()]
        st.write("Months with the highest number of visits:")
        st.dataframe(max_vists_month_df)

        average_time_gym_df = pd.read_sql_query("""
                                SELECT AVG(duration) AS Average_Duration FROM gym_sessions""", db.conn)

        st.write("Average time spent in the gym per session:")
        st.dataframe(average_time_gym_df)

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
    week_grouped_by_df = pd.read_sql_query("""
                      SELECT strftime('%W-%Y', date) AS Year_Week,
                          COUNT(*) AS Session_Count
                        FROM gym_sessions GROUP BY Year_Week""", db.conn)
    st.dataframe(week_grouped_by_df)

    week_count_grouped_df = week_grouped_by_df.groupby('Session_Count').size().reset_index(name='Number_of_Weeks')
    st.dataframe(week_count_grouped_df)

    st.bar_chart(week_count_grouped_df.set_index('Session_Count'))

elif page == "Stats 3":
    st.title("Stats 3")

elif page == "About":
    st.title("About")
    st.write("Something I do because I simply want to. Hurrah!")

elif page == "Logout" and st.session_state.logged_in:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.success("You have been logged out.")
    st.rerun()