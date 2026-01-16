import sqlite3
import os

DB_PATH = r"app/database/medical.db"

def fix_schema():
    print(f"Checking DB at {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("DB file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check 'knowledge_base' table
        cursor.execute("PRAGMA table_info(knowledge_base)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'treatment_type' not in columns:
            print("Adding 'treatment_type' column to knowledge_base...")
            cursor.execute("ALTER TABLE knowledge_base ADD COLUMN treatment_type TEXT DEFAULT 'supportive'")
        else:
            print("'treatment_type' column already exists.")
            
        conn.commit()
        print("Migration complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
