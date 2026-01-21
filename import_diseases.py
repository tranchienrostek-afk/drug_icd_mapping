import sqlite3
import csv
import os
import uuid

DB_PATH = "fastapi-medical-app/app/database/medical.db"
CSV_PATH = "icd_data.csv"

def import_diseases():
    """
    Import diseases from icd_data.csv into the 'diseases' table.
    Schema: id, icd_code, disease_name, chapter_name, slug, search_text, is_active
    """
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure table exists (same as in core.py)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diseases (
            id TEXT PRIMARY KEY,
            icd_code TEXT UNIQUE,
            disease_name TEXT,
            chapter_name TEXT,
            slug TEXT,
            search_text TEXT,
            is_active TEXT DEFAULT 'active'
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_diseases_icd ON diseases(icd_code)")
    
    print(f"Reading {CSV_PATH}...")
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            rows_to_insert = []
            count = 0
            for line_no, row in enumerate(reader):
                if not row or len(row) < 17:
                    continue
                
                # CSV Column mapping (from debug_csv.txt):
                # Col 10: ICD
                # Col 14: Chapter
                # Col 15: Slug/Norm
                # Col 16: Name
                
                icd = row[10].strip()
                chapter = row[14].strip()
                name = row[16].strip()
                slug = row[15].strip() or name.lower()
                
                if not icd or not name:
                    continue
                
                # Generate UUID for id
                disease_id = str(uuid.uuid4())
                
                # Build search_text
                search_text = f"{icd} {name} {slug} {chapter}".lower()
                
                rows_to_insert.append((
                    disease_id,
                    icd,
                    name,
                    chapter,
                    slug,
                    search_text,
                    'active'
                ))
                count += 1
                
            print(f"Parsed {count} diseases.")
            
            # Clear existing and insert
            cursor.execute("DELETE FROM diseases")
            print(f"Cleared old diseases.")
            
            cursor.executemany("""
                INSERT OR REPLACE INTO diseases 
                (id, icd_code, disease_name, chapter_name, slug, search_text, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, rows_to_insert)
            conn.commit()
            print(f"Inserted {cursor.rowcount} rows into diseases table.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_diseases()
