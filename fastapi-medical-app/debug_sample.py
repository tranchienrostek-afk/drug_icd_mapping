import sqlite3
import json

DB_PATH = "app/database/medical.db"

def get_sample_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drugs ORDER BY RANDOM() LIMIT 10")
    rows = [dict(r) for r in cursor.fetchall()]
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    conn.close()

if __name__ == "__main__":
    get_sample_data()
