import os
import sqlite3
from datetime import datetime

# Database file path
db_name = "attendance_data/attendance.db"

# Create attendance_data directory if it doesn't exist
os.makedirs("attendance_data", exist_ok=True)

# Create the database file and table
def init_database():
    # Connect to database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create single attendance table for all records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name VARCHAR(255),
            employee_id VARCHAR(50),
            time_in VARCHAR(255),
            time_out VARCHAR(255),
            status VARCHAR(50),
            date VARCHAR(20)
        )
    ''')
    
    print(f"[+] Database initialized with single attendance table")
    print(f"[+] No CSV files created - only database storage")
    
    # Commit and close
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("[+] Initializing database...")
    init_database()
    print("[+] Database initialization complete!")
    print(f"[+] Database file: {db_name}")
