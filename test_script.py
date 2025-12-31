#!/usr/bin/env python3
"""Full system test script for Week 14.

Checks:
- `log.db` existence
- `system_log` table presence and required columns
- Missing/empty values
- Numeric ranges for CPU, Memory, Disk (0-100)
- Prints summary and saves `test_report.txt`
"""
import os
import sqlite3
import sys
from datetime import datetime

DB_NAME = "log.db"
TABLE_NAME = "system_log"
REQUIRED_METRICS = ["cpu", "memory", "disk"]
REPORT_FILE = "test_report.txt"


def file_exists(path):
    return os.path.isfile(path)


def connect_db(path):
    return sqlite3.connect(path)


def table_exists(conn, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table,))
    return cur.fetchone() is not None


def get_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    return cols


def load_rows(conn, table):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {table}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return cols, rows
    except Exception:
        return [], []


def is_empty_value(val):
    return val is None or (isinstance(val, str) and val.strip() == "")


def safe_float(v):
    try:
        return float(v)
    except Exception:
        return None


def run_tests(save_report=True):
    report_lines = []
    report_lines.append("🔍 Running Full System Test...")

    if not file_exists(DB_NAME):
        report_lines.append("❌ Database file not found: %s" % DB_NAME)
        summary = {
            "total": 0,
            "missing_values": 0,
            "invalid_cpu": 0,
            "invalid_memory": 0,
            "invalid_disk": 0,
            "missing_columns": [],
        }
        report_lines.append("===== Test Summary =====")
        report_lines.append(f"Total Records: {summary['total']}")
        report_lines.append(f"Missing Values: {summary['missing_values']}")
        report_lines.append(f"Invalid CPU Records: {summary['invalid_cpu']}")
        if save_report:
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines) + "\n")
        print("\n".join(report_lines))
        return summary

    conn = connect_db(DB_NAME)

    if not table_exists(conn, TABLE_NAME):
        report_lines.append(f"❌ Table `{TABLE_NAME}` not found in database.")
        if save_report:
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines) + "\n")
        print("\n".join(report_lines))
        return {}

    cols, rows = load_rows(conn, TABLE_NAME)
    total = len(rows)

    report_lines.append("✅ Database file found.")
    report_lines.append(f"✅ Loaded {total} records from {TABLE_NAME}.")

    # Column checks
    missing_columns = [c for c in REQUIRED_METRICS if c not in cols]
    if missing_columns:
        report_lines.append(f"❌ Missing required metric columns: {', '.join(missing_columns)}")
    else:
        report_lines.append("✅ Column check passed.")

    # Missing or empty values
    missing_values = 0
    per_column_missing = {c: 0 for c in cols}

    invalid_cpu = 0
    invalid_memory = 0
    invalid_disk = 0

    for r in rows:
        for i, v in enumerate(r):
            if is_empty_value(v):
                missing_values += 1
                per_column_missing[cols[i]] = per_column_missing.get(cols[i], 0) + 1

        # Validate numeric metrics if present
        row_map = dict(zip(cols, r))
        for metric in REQUIRED_METRICS:
            if metric in row_map:
                val = safe_float(row_map[metric])
                if val is None:
                    if not is_empty_value(row_map[metric]):
                        # non-numeric
                        if metric == "cpu":
                            invalid_cpu += 1
                        elif metric == "memory":
                            invalid_memory += 1
                        elif metric == "disk":
                            invalid_disk += 1
                else:
                    if not (0 <= val <= 100):
                        if metric == "cpu":
                            invalid_cpu += 1
                        elif metric == "memory":
                            invalid_memory += 1
                        elif metric == "disk":
                            invalid_disk += 1

    if missing_values == 0:
        report_lines.append("✅ No missing values detected.")
    else:
        report_lines.append(f"⚠️ Missing values detected: {missing_values} (by column: {per_column_missing})")

    if invalid_cpu + invalid_memory + invalid_disk == 0:
        report_lines.append("✅ All system metrics within valid range (0–100).")
    else:
        report_lines.append("❌ Some metrics out of range or invalid:")
        report_lines.append(f"  - Invalid CPU records: {invalid_cpu}")
        report_lines.append(f"  - Invalid Memory records: {invalid_memory}")
        report_lines.append(f"  - Invalid Disk records: {invalid_disk}")

    # Summary
    report_lines.append("===== Test Summary =====")
    report_lines.append(f"Total Records: {total}")
    report_lines.append(f"Missing Values: {missing_values}")
    report_lines.append(f"Invalid CPU Records: {invalid_cpu}")
    report_lines.append(f"Invalid Memory Records: {invalid_memory}")
    report_lines.append(f"Invalid Disk Records: {invalid_disk}")

    report_lines.append("\n🟢 System validation complete.")

    if save_report:
        try:
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                header = f"System Test Report - {datetime.now().isoformat()}\n"
                f.write(header + "\n".join(report_lines) + "\n")
            report_lines.append(f"Saved report to {REPORT_FILE}")
        except Exception as e:
            report_lines.append(f"Failed to save report: {e}")

    print("\n".join(report_lines))

    conn.close()

    return {
        "total": total,
        "missing_values": missing_values,
        "invalid_cpu": invalid_cpu,
        "invalid_memory": invalid_memory,
        "invalid_disk": invalid_disk,
        "missing_columns": missing_columns,
    }


if __name__ == "__main__":
    save = True
    # allow optional --no-save
    if "--no-save" in sys.argv:
        save = False
    run_tests(save_report=save)
