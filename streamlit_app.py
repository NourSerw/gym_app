import datetime
import streamlit as st
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

from db.db import database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Initialize database
db = database()

def to_seconds(t):
    if not t:                
        return None
    try:
        h, m, s = t.split(':')
        return int(h)*3600 + int(m)*60 + float(s)
    except Exception:
        return None

def from_seconds(sec):
    return str(datetime.timedelta(seconds=sec))

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
    page = st.sidebar.radio("Go to", ["Gym Tracker", "Change Data","Stats 1", "Stats 2", "Stats 3", "About", "Logout"])
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
                           SELECT date AS Date, category AS Category, 
                           gym_name AS Gym, duration AS Duration
                           FROM gym_sessions""", db.conn)
    st.dataframe(df)
elif page == "Change Data":
    """Page to change the data. Now includes insert and delete."""
    gym_sessions = pd.read_sql_query("SELECT * FROM gym_sessions", db.conn)

    st.title("Insert Record(s)")
    with st.form("insert_form"):
        date = st.text_input("Date (YYYY-MM-DD)")
        duration = st.text_input("Duration (HH:MM:SS)")
        gym_name = st.text_input("Gym Name")
        category = st.text_input("Category")
        submitted = st.form_submit_button("Insert Record")
    
        if submitted:
            if duration and gym_name and category:
                insert_status = db.insert_gym_session(date, duration, gym_name, category)
                if insert_status:
                    st.success("Record inserted successfully!")
                else:
                    st.error("Failed to insert record. Please check your input.")
            else:
                st.error("Please fill in all fields.")

    
    st.title("Delete Record(s)")
    value = st.selectbox(
        "Select date to delete",
        sorted(gym_sessions['date'].dropna().unique()))
    filtered_df = gym_sessions[gym_sessions['date'] == value]
    st.subheader("Filtered Rows")
    st.dataframe(filtered_df)
    if st.button("Delete Dates"):
        db.cursor("DELETE FROM gym_sessions WHERE date = ?", (filtered_df['date']))
        db.conn.commit()

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
                                SELECT duration FROM gym_sessions WHERE duration IS NOT NULL""", db.conn)
        average_time_gym_df['Duration_Seconds'] = average_time_gym_df['duration'].apply(to_seconds)
        average_seconds = average_time_gym_df['Duration_Seconds'].mean()
        average_time_gym_df = pd.DataFrame({
            'Average_Duration': [from_seconds(average_seconds)]
        })  

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
                      SELECT strftime('%W-%Y', date) AS Week_Year,
                          COUNT(*) AS Session_Count
                        FROM gym_sessions GROUP BY Week_Year""", db.conn)
    st.dataframe(week_grouped_by_df)

    week_count_grouped_df = week_grouped_by_df.groupby('Session_Count').size().reset_index(name='Number_of_Weeks')
    st.dataframe(week_count_grouped_df)

    st.bar_chart(week_count_grouped_df.set_index('Session_Count'))

elif page == "Stats 3":
    st.title("Stats 3")
    days_stats_df = pd.read_sql_query("""
                                      SELECT julianday(date()) - julianday(min(date)) AS 'Total Days',
                                      julianday(max(date)) - julianday(min(date)) AS 'Logged Days',
                                      ROUND((julianday(max(date)) - julianday(min(date))) / 7.0, 0) AS 'Total Weeks',
                                      ROUND((julianday(max(date)) - julianday(min(date))) / 30.0, 0) AS 'Total Months',
                                      (COUNT(*) / ROUND((julianday(max(date)) - julianday(min(date))) / 7.0, 0)) AS 'Avg Sessions per Week',
                                      (COUNT(*) / ROUND((julianday(max(date)) - julianday(min(date))) / 30.0, 0)) AS 'Avg Sessions per Month'
                                      FROM gym_sessions
                                      """, db.conn)
    st.dataframe(days_stats_df)

    other_stats_df = pd.read_sql_query("""
                                      SELECT ROUND((julianday(max(date)) - julianday(min(date))) / 365.0, 0) AS 'Total Years',
                                      COUNT(*) / ROUND((julianday(max(date)) - julianday(min(date))) / 365.0, 0) AS 'Average Sessions per Year'
                                      FROM gym_sessions
                                      """, db.conn)
    st.dataframe(other_stats_df)

elif page == "About":
    st.title("About")
    st.write("Something I do because I simply want to. Hurrah!")

elif page == "Logout" and st.session_state.logged_in:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.success("You have been logged out.")
    st.rerun()