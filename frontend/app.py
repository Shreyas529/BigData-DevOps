import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import subprocess
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "Testing")

# ========================
#  DB Connection Function
# ========================
def get_connection():
    return psycopg2.connect(
        host="postgres",
        database="netflix",
        user="postgres",
        password="postgres",
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
#  Fetch Region & Device Insights
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
# Call Producer Script
# ========================
def call_producer(rate, duration):
    producer_path = os.path.join("..", "data_generator", "producer.py")

    # In Docker/K8s, producer will be a container call
    if ENVIRONMENT == "Testing":
        st.info(f"Pretending to generate data ({rate} eps, {duration}s)...")
        time.sleep(2)
        return "TEST MODE: Simulated producer call"

    # Actual execution (local or container-based)
    try:
        out = subprocess.check_output(
            ["python", producer_path, "--rate", str(rate), "--duration", str(duration)],
            stderr=subprocess.STDOUT,
            text=True
        )
        return out
    except Exception as e:
        return f"❌ Failed to run producer: {e}"

# ========================
#  STREAMLIT UI
# ========================
st.set_page_config(page_title="Netflix Analytics", layout="wide")

st.title("📊 Netflix Login Analytics (Batch + Kafka + PostgreSQL)")
st.write("Generate data → Kafka → PostgreSQL → Query & Visualize")

# ========== Data Generator Controls ==========
st.sidebar.header("⚙ Data Generation Controls")

rate = st.sidebar.number_input("Throughput (events/sec)", min_value=1, max_value=5000, value=50)
duration = st.sidebar.number_input("Generate Duration (seconds)", min_value=1, max_value=600, value=10)

if st.sidebar.button("🚀 Generate Data"):
    output = call_producer(rate, duration)
    st.sidebar.success(f"Triggered Data Generation:\n{output}")

# ========== Charts ==========
refresh_rate = st.sidebar.slider("Refresh Dashboard Every (seconds):", 5, 60, 10)

st.subheader("👥 Unique Active Users (Last 50 Windows)")
data = fetch_unique_users()

if data.empty:
    st.warning("No data yet from Kafka Consumer. Waiting for events...")
else:
    data = data.sort_values("window_start")
    st.line_chart(data.set_index("window_start"))

# ========== Region Breakdown ==========
st.subheader("🌍 Login Distribution by Region")
region_df = fetch_region_insights()
col1, col2 = st.columns(2)
with col1:
    st.bar_chart(region_df.set_index("region"))

# ========== Device Breakdown ==========
device_df = fetch_device_insights()
with col2:
    st.bar_chart(device_df.set_index("device"))

st.write("⚙ Backend processor consumes Kafka events → Writes to PostgreSQL → This Dashboard reads results.")

# Auto refresh
time.sleep(refresh_rate)
st.experimental_rerun()
