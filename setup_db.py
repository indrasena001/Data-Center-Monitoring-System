import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "log.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create system_log table
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu REAL,
            memory REAL,
            disk REAL
        )
    ''')
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    # Generate dummy data for logs
    print("Generating dummy data...")
    base_time = datetime.now()
    for i in range(50):
        timestamp = (base_time - timedelta(minutes=i*5)).strftime('%Y-%m-%d %H:%M:%S')
        cpu = round(random.uniform(10, 90), 1)
        memory = round(random.uniform(20, 80), 1)
        disk = round(random.uniform(30, 70), 1)
        
        c.execute("INSERT INTO system_log (timestamp, cpu, memory, disk) VALUES (?, ?, ?, ?)",
                  (timestamp, cpu, memory, disk))
    
    # Insert default users
    users = [
        ("admin", "admin123", "admin"),
        ("user", "user123", "user")
    ]
    
    for username, password, role in users:
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        except sqlite3.IntegrityError:
            pass # User already exists

    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' created successfully with 50 records and default users.")

if __name__ == "__main__":
    create_db()

