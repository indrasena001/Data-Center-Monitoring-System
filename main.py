import sqlite3
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os

DB_NAME = "log.db"

# TODO: Define your bonus features here
# Example 1: Calculate how many times CPU > 80%
# Example 2: Send alert email if CPU > 90%
# Example 3: Generate text summary report with top 3 CPU peaks

def load_data():
    if not os.path.exists(DB_NAME):
        print("Database not found. Please ensure log.db exists.")
        return None
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM system_log", conn)
    conn.close()
    return df

def count_high_cpu(df):
    # Try to find a CPU column (case-insensitive common names)
    cpu_cols = [c for c in df.columns if c.lower() in ("cpu", "cpu_usage", "cpu%", "cpu_pct", "usage_cpu")]
    if not cpu_cols:
        # Fallback: any column with 'cpu' substring
        cpu_cols = [c for c in df.columns if "cpu" in c.lower()]
    if not cpu_cols:
        raise ValueError("No CPU column found in dataframe")
    cpu_col = cpu_cols[0]

    # Ensure numeric
    df[cpu_col] = pd.to_numeric(df[cpu_col], errors="coerce")

    count_over_80 = int((df[cpu_col] > 80).sum())
    count_over_90 = int((df[cpu_col] > 90).sum())
    return {"cpu_col": cpu_col, ">80": count_over_80, ">90": count_over_90}

def generate_summary(df):
    # Build a text summary containing metrics requested in the spec
    total = len(df)

    # CPU handling (reuse count_high_cpu to find column)
    cpu_info = count_high_cpu(df)
    cpu_col = cpu_info["cpu_col"]

    # Numeric conversion (safe)
    df[cpu_col] = pd.to_numeric(df[cpu_col], errors="coerce")
    avg_cpu = float(df[cpu_col].mean()) if total > 0 else 0.0
    max_cpu = float(df[cpu_col].max()) if total > 0 else 0.0

    # Top 3 peaks
    peaks = df[cpu_col].dropna().sort_values(ascending=False).head(3).tolist()

    # Network DOWN count: try to detect a network/status column
    net_cols = [c for c in df.columns if "network" in c.lower() or "status" == c.lower()]
    net_down_count = 0
    if net_cols:
        col = net_cols[0]
        net_down_count = int(df[col].astype(str).str.lower().str.contains("down").sum())

    summary_lines = [
        "**System Summary**",
        f"Total Records: {total}",
        f"Average CPU Usage: {avg_cpu:.2f}%",
        f"Maximum CPU Usage: {max_cpu}",
        f"Network DOWN count: {net_down_count}",
        f"Top 3 CPU Peaks: {peaks}",
        f"⚠️ ALERT: {cpu_info['>90']} records exceeded 90% CPU usage.",
    ]

    summary_text = "\n\n".join(summary_lines)
    return summary_text

def send_email_alert(message):
    # Simulate sending an email. If SMTP env vars are configured, attempt send.
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "0")) if os.environ.get("SMTP_PORT") else None
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    print("--- Simulated Email Alert ---")
    print(message)
    print("--- End Simulated Email ---")

    # If SMTP details present, try to send a real email (best-effort)
    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = MIMEText(message)
            msg["Subject"] = "CPU Alert"
            msg["From"] = smtp_user
            msg["To"] = smtp_user
            s = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, [smtp_user], msg.as_string())
            s.quit()
            print("Email sent via SMTP")
        except Exception as e:
            print(f"Failed to send SMTP email: {e}")

if __name__ == "__main__":
    df = load_data()
    if df is not None:
        try:
            counts = count_high_cpu(df)
            summary = generate_summary(df)

            # Print summary to console
            print(summary)

            # Save summary to file
            with open("summary.txt", "w", encoding="utf-8") as f:
                f.write(summary)

            # Simulate/send email if any record >90
            if counts[">90"] > 0:
                send_email_alert(summary)
        except Exception as e:
            print(f"Error generating summary: {e}")
