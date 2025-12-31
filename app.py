import streamlit as st
import sqlite3
import pandas as pd
import time
import os

DB_NAME = "log.db"

st.set_page_config(page_title="Data Center Monitoring System", layout="wide")

# Custom CSS for animated background and styling
st.markdown("""
<style>
    /* Animated Gradient Background - Deeper, richer colors */
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #141E30);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    @keyframes gradient {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }

    /* Glassmorphism Card Style for Containers - Darker for better text visibility */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background: rgba(0, 0, 0, 0.6); /* Darker background */
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    
    /* Input Fields Styling */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.9); /* Lighter background */
        color: black; /* Black text/dots */
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stTextInput > div > div > input:focus {
        border-color: #00c6ff; /* Cyan focus border */
        box-shadow: 0 0 10px rgba(0, 198, 255, 0.5);
        color: black;
    }
    
    /* Button Styling - New Colors (Purple/Blue) */
    .stButton > button {
        background: linear-gradient(45deg, #8E2DE2 0%, #4A00E0 100%); /* Purple to Blue */
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 20px;
        width: 100%;
        min-height: 56px;
        height: 56px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(74, 0, 224, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(74, 0, 224, 0.6);
        background: linear-gradient(45deg, #9b42f5 0%, #5d11f7 100%); /* Lighter on hover */
    }

    /* Download Button Styling - Green */
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(45deg, #11998e 0%, #38ef7d 100%); /* Green Gradient */
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 30px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4);
    }

    div[data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(56, 239, 125, 0.6);
        background: linear-gradient(45deg, #16a085 0%, #2ecc71 100%);
    }
    
    /* Text Colors & Visibility */
    h1, h2, h3, h4, h5, h6 {
        color: #00c6ff !important; /* Cyan Headers */
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    
    p, label, .stMarkdown, .stText {
        color: #e0e0e0 !important; /* Off-white for body text */
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Dataframe Styling */
    div[data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        backdrop-filter: blur(5px);
        z-index: 1000;
    }
    
</style>
<div class="footer">
    <p>© 2025 Indrasena. All Rights Reserved.</p>
</div>
""", unsafe_allow_html=True)

# Dark mode CSS (optional toggle)
dark_css = """
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b1220 !important;
    color: #e6eef6 !important;
}
.stApp, .main, .block-container {
    background-color: #0b1220 !important;
    color: #e6eef6 !important;
}
.css-1d391kg, .css-1v3fvcr {
    background-color: transparent !important;
}
.stButton>button {
    background-color: #1f2a44 !important;
    color: #e6eef6 !important;
}
</style>
"""

# Inject dark mode CSS when enabled in session state
if st.session_state.get("dark_mode"):
    st.markdown(dark_css, unsafe_allow_html=True)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "just_logged_in" not in st.session_state:
    st.session_state.just_logged_in = False

# Initialize thresholds in session state
if "cpu_threshold" not in st.session_state:
    st.session_state.cpu_threshold = 80
if "memory_threshold" not in st.session_state:
    st.session_state.memory_threshold = 85
if "disk_threshold" not in st.session_state:
    st.session_state.disk_threshold = 90

def check_password():
    """Checks if the password is correct using the database."""
    username = st.session_state["username"]
    password = st.session_state["password"]
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Ensure users table exists or handle error
    try:
        c.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
    except sqlite3.OperationalError:
        st.error("Table 'users' not found in database. Please ensure the database is set up correctly.")
        user = None
    finally:
        conn.close()
    
    if user:
        st.session_state.logged_in = True
        st.session_state.role = user[0]
        st.session_state.just_logged_in = True
        del st.session_state["password"]  # don't store password
    else:
        st.session_state.logged_in = False
        st.error("😕 User not known or password incorrect")

if not st.session_state.logged_in:
    # Glassy title at the top
    st.markdown("""
    <style>
    .glassy-title {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    .glassy-title h1 {
        color: #00c6ff !important;
        font-size: 48px !important;
        font-weight: 900 !important;
        margin: 0 !important;
        text-shadow: 0 2px 10px rgba(0, 198, 255, 0.3);
    }
    </style>
    <div class="glassy-title">
        <h1>🖥️ Data Center Monitoring System</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Pre-login layout with image on left
    img_col, form_col = st.columns([1, 1])
    
    with img_col:
        try:
            st.image("Image.png", use_container_width=True, caption="Data Center Monitoring System")
        except Exception:
            pass
    
    with form_col:
        st.title("🔐 Login")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password", on_change=check_password)
        st.button("Login", on_click=check_password)

else:
    # If user just logged in, show a brief loading/rendering animation
    if st.session_state.get("just_logged_in"):
        with st.spinner("Rendering dashboard..."):
            progress = st.progress(0)
            for i, p in enumerate(range(0, 101, 5)):
                progress.progress(p)
                time.sleep(0.03)
        st.session_state.just_logged_in = False

    st.title(f"Welcome, {st.session_state.get('username', 'User')}")

    # Navigation
    st.sidebar.title(f"📂 Navigation ({st.session_state.role})")
    
    options = ["Dashboard", "Networking", "Logout"]
    if st.session_state.role == "admin":
        options.insert(1, "Configuration")

    page = st.sidebar.radio("Select Page", options)

    if page == "Dashboard":
        # Check if database exists
        if not os.path.exists(DB_NAME):
            st.warning("Database not found. Please ensure 'log.db' from Week 7–11 exists.")
        else:
            # Connect to database and load system_log table
            try:
                conn = sqlite3.connect(DB_NAME)
                df = pd.read_sql_query("SELECT * FROM system_log", conn)
                conn.close()
        
                if df.empty:
                    st.warning("The database is empty. No logs to analyze.")
                else:
                    st.title("📊 System Log Analysis & Reporting")
        
                    # Ensure timestamp is datetime
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
                    # --- Statistics Calculation ---
                    avg_cpu = df['cpu'].mean()
                    avg_memory = df['memory'].mean()
                    avg_disk = df['disk'].mean()
        
                    # Use dynamic thresholds from session state
                    cpu_alerts = df[df['cpu'] > st.session_state.cpu_threshold].shape[0]
                    memory_alerts = df[df['memory'] > st.session_state.memory_threshold].shape[0]
                    disk_alerts = df[df['disk'] > st.session_state.disk_threshold].shape[0]
        
                    # --- Display Key Statistics ---
                    st.subheader("Key Metrics")

                    def metric_card(label, value, color):
                        st.markdown(f"""
                        <div style="
                            background-color: rgba(255, 255, 255, 0.05);
                            padding: 15px;
                            border-radius: 10px;
                            border-left: 5px solid {color};
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                            text-align: center;
                            margin-bottom: 10px;
                        ">
                            <p style="color: #e0e0e0; margin: 0; font-size: 16px; font-weight: bold;">{label}</p>
                            <p style="color: {color}; margin: 5px 0 0 0; font-size: 24px; font-weight: bold;">{value}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        metric_card("Average CPU", f"{avg_cpu:.2f}%", "#00c6ff") # Cyan
                    with col2:
                        metric_card("Average Memory", f"{avg_memory:.2f}%", "#8E2DE2") # Purple
                    with col3:
                        metric_card("Average Disk", f"{avg_disk:.2f}%", "#FF416C") # Pink/Red

                    col4, col5, col6 = st.columns(3)
                    with col4:
                        color = "#FF4B2B" if cpu_alerts > 0 else "#00b09b" # Red if alerts, else Green
                        metric_card(f"CPU Alerts (>{st.session_state.cpu_threshold}%)", cpu_alerts, color)
                    with col5:
                        color = "#FF4B2B" if memory_alerts > 0 else "#00b09b"
                        metric_card(f"Memory Alerts (>{st.session_state.memory_threshold}%)", memory_alerts, color)
                    with col6:
                        color = "#FF4B2B" if disk_alerts > 0 else "#00b09b"
                        metric_card(f"Disk Alerts (>{st.session_state.disk_threshold}%)", disk_alerts, color)
        
                    # --- Charts ---
                    st.subheader("📈 System Resource Trends")
                    if 'timestamp' in df.columns:
                        chart_data = df.set_index("timestamp")[["cpu", "memory", "disk"]]
                        st.line_chart(chart_data)
                    else:
                        st.line_chart(df[["cpu", "memory", "disk"]])
        
                    # --- Report Generation ---
                    st.subheader("📝 Generate Report")
                    
                    report_data = {
                        "Metric": [
                            "Average CPU", "Average Memory", "Average Disk",
                            "CPU Alerts", "Memory Alerts", "Disk Alerts"
                        ],
                        "Value": [
                            f"{avg_cpu:.2f}%", f"{avg_memory:.2f}%", f"{avg_disk:.2f}%",
                            str(cpu_alerts), str(memory_alerts), str(disk_alerts)
                        ]
                    }
                    report_df = pd.DataFrame(report_data)
                    
                    st.table(report_df)
        
                    csv = report_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Report as CSV",
                        data=csv,
                        file_name="system_report.csv",
                        mime="text/csv",
                    )
        
                    # --- Bonus: Alert History ---
                    st.subheader("⚠️ Alert History (Last 24 Hours)")
                    # Assuming 'timestamp' exists and is datetime
                    if 'timestamp' in df.columns:
                         # Filter for alerts
                        alerts_df = df[
                            (df['cpu'] > 80) | 
                            (df['memory'] > 85) | 
                            (df['disk'] > 90)
                        ].copy()
                        
                        if not alerts_df.empty:
                            st.dataframe(alerts_df.sort_values(by="timestamp", ascending=False))
                        else:
                            st.info("No alerts found in the logs.")
        
            except Exception as e:
                st.error(f"An error occurred: {e}")

    elif page == "Networking":
        st.title("🌐 Interactive Data Center Dashboard")

        # Check if database exists
        if not os.path.exists(DB_NAME):
            st.warning("Database not found. Please make sure 'log.db' from Week 7–8 exists.")
        else:
            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query("SELECT * FROM system_log", conn)
            # Ensure timestamp is parsed
            if "timestamp" in df.columns:
                try:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                except Exception:
                    pass

            # Refresh controls
            if st.sidebar.button("Refresh"):
                rerun = getattr(st, "experimental_rerun", None)
                if callable(rerun):
                    rerun()

            # Filters in the sidebar
            st.sidebar.markdown("### Filters")
            ping_filter = st.sidebar.selectbox("Ping Status", ["All", "UP", "DOWN"], index=0)
            cpu_threshold = st.sidebar.slider("CPU Threshold (%)", 0, 100, 0)
            # Optional: date filter (bonus)
            try:
                min_date = df["timestamp"].min().date()
                max_date = df["timestamp"].max().date()
                date_range = st.sidebar.date_input("Date range", value=(min_date, max_date))
            except Exception:
                date_range = None

            # Apply filters
            df_filtered = df.copy()
            if ping_filter != "All" and "ping_status" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["ping_status"] == ping_filter]
            if "cpu" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["cpu"] >= cpu_threshold]
            if date_range and isinstance(date_range, tuple) and "timestamp" in df_filtered.columns:
                start_dt = pd.to_datetime(date_range[0])
                end_dt = pd.to_datetime(date_range[1])
                end_dt = end_dt + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df_filtered = df_filtered[(df_filtered["timestamp"] >= start_dt) & (df_filtered["timestamp"] <= end_dt)]

            st.subheader("Filtered Records")
            if df_filtered.empty:
                st.info("No records match the selected filters.")
            else:
                st.dataframe(df_filtered, width="stretch")

            # Alert count: records where cpu exceeds threshold OR ping is DOWN
            alert_count = 0
            if not df.empty:
                cond_cpu = df.get("cpu") > cpu_threshold if "cpu" in df.columns else pd.Series(False, index=df.index)
                cond_ping = df.get("ping_status") == "DOWN" if "ping_status" in df.columns else pd.Series(False, index=df.index)
                alert_count = int((cond_cpu | cond_ping).sum())

            col1, col2 = st.columns(2)
            col1.metric("Total records", len(df))
            col2.metric("Alert count", alert_count)

            # Charts
            st.subheader("📈 Resource Usage Over Time")
            if "timestamp" in df_filtered.columns and not df_filtered.empty:
                chart_df = df_filtered.set_index("timestamp")[ [c for c in ["cpu", "memory", "disk"] if c in df_filtered.columns] ]
                if not chart_df.empty:
                    st.line_chart(chart_df)
            else:
                st.info("No time-series data available for the selected filters.")

            conn.close()

    elif page == "Configuration":
        if st.session_state.role != "admin":
            st.error("Access Denied")
        else:
            st.title("⚙️ Configuration Panel")
            st.write("Adjust the alert thresholds for system metrics.")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state.cpu_threshold = st.slider(
                    "CPU Alert Threshold (%)", 0, 100, st.session_state.cpu_threshold
                )
            with col2:
                st.session_state.memory_threshold = st.slider(
                    "Memory Alert Threshold (%)", 0, 100, st.session_state.memory_threshold
                )
            with col3:
                st.session_state.disk_threshold = st.slider(
                    "Disk Alert Threshold (%)", 0, 100, st.session_state.disk_threshold
                )
            
            # Dark mode toggle
            st.checkbox("Dark Mode", key="dark_mode")

            st.success("Configuration saved automatically!")

    elif page == "Logout":
        st.title("Log out")
        st.write("Are you sure you want to log out?")
        if st.button("Confirm Logout"):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.rerun()

    # --- Bottom: Quick access buttons for Summary and Test Report ---
    def _show_summary():
        st.session_state.show_summary = True

    def _show_test_report():
        st.session_state.show_test_report = True

    if "show_summary" not in st.session_state:
        st.session_state.show_summary = False
    if "show_test_report" not in st.session_state:
        st.session_state.show_test_report = False

    # Display file contents if requested (kept at bottom)
    if st.session_state.show_summary:
        try:
            with open("summary.txt", "r", encoding="utf-8") as f:
                content = f.read()
            st.subheader("Summary")
            st.code(content)
            st.download_button("Download Summary", data=content, file_name="summary.txt", mime="text/plain")
        except Exception as e:
            st.error(f"Could not read summary.txt: {e}")

    if st.session_state.show_test_report:
        try:
            with open("test_report.txt", "r", encoding="utf-8") as f:
                content = f.read()
            st.subheader("Test Report")
            st.code(content)
            st.download_button("Download Test Report", data=content, file_name="test_report.txt", mime="text/plain")
        except Exception as e:
            st.error(f"Could not read test_report.txt: {e}")

    # Buttons placed at the very bottom (equal size)
    st.markdown("---")
    btn_col1, btn_col2 = st.columns([1,1])
    with btn_col1:
        st.button("Summary", on_click=_show_summary)
    with btn_col2:
        st.button("Test Report", on_click=_show_test_report)
