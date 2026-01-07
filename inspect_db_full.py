import sqlite3
import os

db_path = 'fastapi-medical-app/app/database/medical.db'
output_path = 'schema_dump_utf8.txt'

def get_schema():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for table_name in tables:
            f.write(f"--- Table: {table_name} ---\n")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = cursor.fetchall()
            for col in cols:
                f.write(f"  Col: {col}\n")
                
            # Get creation SQL
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_sql = cursor.fetchone()[0]
            f.write(f"  SQL: {create_sql}\n\n")
            
    conn.close()
    print(f"Schema dumped to {output_path}")

if __name__ == "__main__":
    get_schema()
