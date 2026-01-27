
import sqlite3
import os

DB_PATH = "app/database/medical.db"

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM diseases")
    count = cursor.fetchone()[0]
    print(f"DEBUG_COUNT_RESULT:{count}")
except Exception as e:
    print(f"DEBUG_ERROR:{e}")
finally:
    if 'conn' in locals(): conn.close()
