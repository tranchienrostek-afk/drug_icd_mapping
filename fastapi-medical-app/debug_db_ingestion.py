import sqlite3
import os

db_path = "app/database/medical.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_base';")
    table = cursor.fetchone()
    if not table:
        print("Table 'knowledge_base' DOES NOT EXIST!")
    else:
        print("Table 'knowledge_base' exists.")
        
        # Count rows
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        count = cursor.fetchone()[0]
        print(f"Total rows in knowledge_base: {count}")
        
        if count > 0:
            cursor.execute("SELECT drug_name FROM knowledge_base ORDER BY id DESC LIMIT 5")
            print("Recent rows:", cursor.fetchall())

    conn.close()
except Exception as e:
    print(f"Error querying database: {e}")
