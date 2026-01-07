import sqlite3
import os

DB_PATH = "fastapi-medical-app/app/database/medical.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"DB NOT FOUND at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Diseases Schema ---")
    cursor.execute("PRAGMA table_info(diseases)")
    cols = cursor.fetchall()
    found_cols = [c[1] for c in cols]
    print(found_cols)
    
    conn.close()

if __name__ == "__main__":
    check_db()
