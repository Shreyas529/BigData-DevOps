import streamlit as st
import random
import time
import requests
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

# Available regions
REGIONS = ["US", "IN", "UK", "DE", "CA", "FR", "JP", "AU", "BR", "MX"]

def send_login_event(username: str, region: str, status: str):
    """Send login event to backend service"""
    try:
        payload = {
            "username": username,
            "region": region,
            "status": status
        }
        response = requests.post(
            f"{BACKEND_URL}/api/login-event",
            json=payload,
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.warning(f"Failed to send login event: {e}")
        return False

def login_page():
    """Display the login page"""
    st.title("🔐 Login")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        region = st.selectbox("Select Region", options=REGIONS, index=0)
        
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                # Determine login success with 70% probability
                login_success = random.random() < 0.7
                status = "success" if login_success else "failed"
                
                # Send login event to backend
                send_login_event(username, region, status)
                
                # Store result in session state
                st.session_state.logged_in = login_success
                st.session_state.username = username
                st.session_state.region = region
                st.rerun()

def success_page():
    """Display the login success page"""
    st.title("✅ Login Successful!")
    st.markdown("---")
    st.success(f"Welcome, **{st.session_state.username}**!")
    st.info(f"You are logged in from region: **{st.session_state.region}**")
    
    st.balloons()
    
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = None
        st.session_state.username = None
        st.session_state.region = None
        st.rerun()

def failure_page():
    """Display the login failure page"""
    st.title("❌ Login Failed")
    st.markdown("---")
    st.error("Invalid credentials. Please try again.")
    st.warning(f"Attempted login from region: **{st.session_state.region}**")
    
    if st.button("Try Again", use_container_width=True):
        st.session_state.logged_in = None
        st.session_state.username = None
        st.session_state.region = None
        st.rerun()

def main():
    st.set_page_config(
        page_title="Login Portal",
        page_icon="🔐",
        layout="centered"
    )
    
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "region" not in st.session_state:
        st.session_state.region = None
    
    # Route to appropriate page
    if st.session_state.logged_in is None:
        login_page()
    elif st.session_state.logged_in:
        success_page()
    else:
        failure_page()

if __name__ == "__main__":
    main()
