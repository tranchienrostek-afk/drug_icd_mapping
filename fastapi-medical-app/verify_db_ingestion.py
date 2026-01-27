import sqlite3
import os

# Path to the database on the host (since volume is mounted)
db_path = "app/database/medical.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query for the test data
    cursor.execute("SELECT * FROM knowledge_base WHERE drug_name LIKE 'Paracetamol%' OR drug_name LIKE 'Amoxicillin%' ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} rows matching test data:")
    for row in rows:
        print(dict(row))
        
    conn.close()
except Exception as e:
    print(f"Error querying database: {e}")
