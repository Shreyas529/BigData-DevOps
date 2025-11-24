import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import time

ENVIRONMENT = "Testing" 

# ========================
#  DB Connection Function
# ========================
def get_connection():
    return psycopg2.connect(
        host="postgres",        # service name in docker-compose or k8s
        database="netflix",
        user="postgres",
        password="postgres",    # change later & store in Vault/K8s Secrets
        cursor_factory=RealDictCursor
    )

# ========================
#  Fetch Aggregated Data
# ========================
def fetch_unique_users():

    if ENVIRONMENT == "Testing":
        return pd.DataFrame({
            "window_start": pd.date_range(start="2023-01-01", periods=50, freq="10S"),
            "unique_users": range(1, 51)
        })

    query = """
    SELECT window_start, unique_users
    FROM mv_unique_users_10s
    ORDER BY window_start DESC
    LIMIT 50;
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(rows)

# ========================
#  Fetch Filter Insights
# ========================
def fetch_region_insights():

    if ENVIRONMENT == "Testing":
        return pd.DataFrame({
            "region": ["US", "CA", "MX", "BR", "AR"],
            "logins": [10, 20, 30, 40, 50]
        })

    query = """
    SELECT region, COUNT(*) AS logins
    FROM user_login_events
    GROUP BY region ORDER BY logins DESC;
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(rows)

def fetch_device_insights():

    if ENVIRONMENT == "Testing":
        return pd.DataFrame({
            "device": ["Desktop", "Mobile", "Tablet", "TV", "Other"],
            "logins": [10, 20, 30, 40, 50]
        })

    query = """
    SELECT device, COUNT(*) AS logins
    FROM user_login_events
    GROUP BY device ORDER BY logins DESC;
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(rows)


# ========================
#  STREAMLIT UI
# ========================
st.set_page_config(page_title="Netflix Analytics", layout="wide")

st.title("📊 Netflix Real-Time Login Analytics (Batch + Kafka + PostgreSQL)")
st.write("Showing login analytics generated from Kafka and stored in PostgreSQL.")

refresh_rate = st.sidebar.slider("Refresh Every (seconds):", 5, 60, 10)

# ========================
#  SECTION 1: Unique User Chart
# ========================
st.subheader("👥 Unique Active Users (Last 50 Windows)")
data = fetch_unique_users()

if data.empty:
    st.warning("No data yet from Kafka Consumer. Waiting for events...")
else:
    data = data.sort_values("window_start")
    st.line_chart(data.set_index("window_start"))

# ========================
#  SECTION 2: Region Breakdown
# ========================
st.subheader("🌍 Login Distribution by Region")
region_df = fetch_region_insights()

col1, col2 = st.columns(2)

with col1:
    st.bar_chart(region_df.set_index("region"))

# ========================
#  SECTION 3: Device Breakdown
# ========================
device_df = fetch_device_insights()

with col2:
    st.bar_chart(device_df.set_index("device"))

st.write("⚙ Backend Consumer writes events into PostgreSQL → This UI queries aggregated results.")

# Auto refresh
time.sleep(refresh_rate)
st.experimental_rerun()
