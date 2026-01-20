import sqlite3
import csv
import os
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "app/database/medical.db")
CSV_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\to_database\icd_data.csv"

def normalize_text(text):
    if not text: return ""
    return str(text).strip()

def run_import():
    print(f"--- Import Diseases from icd_data.csv ---")
    print(f"DB: {DB_PATH}")
    print(f"CSV: {CSV_PATH}")

    if not os.path.exists(CSV_PATH):
        print("❌ CSV File not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Create Table (Strict Spec)
        print("Creating table `diseases`...")
        cursor.execute("DROP TABLE IF EXISTS diseases")
        cursor.execute("""
            CREATE TABLE diseases (
                id TEXT PRIMARY KEY,
                icd_code TEXT UNIQUE,
                disease_name TEXT,
                chapter_name TEXT,
                slug TEXT,
                search_text TEXT,
                is_active TEXT DEFAULT 'active'
            )
        """)
        
        # FTS Table
        cursor.execute("DROP TABLE IF EXISTS diseases_fts")
        cursor.execute("""
            CREATE VIRTUAL TABLE diseases_fts USING fts5(
                icd_code, disease_name, search_text,
                content='diseases', content_rowid='rowid'
            )
        """)
        conn.commit()

        # 2. Import Data
        print("Reading CSV...")
        count = 0
        skipped = 0
        
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # No header in file, so no next(reader)
            
            for row in reader:
                try:
                    # Index Mapping based on inspection
                    # Col 0: ID
                    # Col 10: ICD Code
                    # Col 14: Chapter
                    # Col 15: Slug
                    # Col 16: Name
                    
                    if len(row) < 17:
                        skipped += 1
                        continue

                    r_id = normalize_text(row[0])
                    icd = normalize_text(row[10])
                    chapter = normalize_text(row[14])
                    slug = normalize_text(row[15])
                    name = normalize_text(row[16])
                    
                    if not r_id or not icd:
                        skipped += 1
                        continue
                        
                    # Search text
                    search_text = f"{icd} {name} {slug} {chapter}".lower().strip()
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO diseases (
                            id, icd_code, disease_name, chapter_name, slug, search_text, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active')
                    """, (r_id, icd, name, chapter, slug, search_text))
                    
                    count += 1
                    if count % 1000 == 0:
                        print(f"Imported {count}...", end='\r')
                        
                except Exception as row_err:
                    print(f"Row Error: {row_err}")
                    skipped += 1

        conn.commit()
        print(f"\n✅ SUCCESS: Imported {count} diseases.")
        print(f"❌ Skipped: {skipped}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_import()
