import sqlite3
import csv
import os

DB_PATH = "fastapi-medical-app/app/database/medical.db"
CSV_PATH = "knowledge for agent/to_database/icd_data.csv"

def import_diseases():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Reading {CSV_PATH}...")
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            rows_to_insert = []
            count = 0
            for line_no, row in enumerate(reader):
                if not row or len(row) < 16:
                    continue
                
                # Inspecting debug_csv.txt:
                # Col 10: ICD
                # Col 14: Chapter
                # Col 15: Slug/Norm
                # Col 16: Name
                
                if len(row) < 17:
                    continue

                icd = row[10].strip()
                chapter = row[14].strip()
                name = row[16].strip()
                slug = row[15].strip()
                
                if not icd or not name:
                    continue
                
                # Insert into knowledge_base
                rows_to_insert.append((
                    icd,
                    name,
                    slug if slug else name.lower(), # norm
                    chapter,
                    "_ICD_LIST_", # drug_name
                    "_icd_list_", # drug_name_norm
                    0             # frequency
                ))
                count += 1
                
            print(f"Parsed {count} diseases.")
            
            query = """
            INSERT INTO knowledge_base 
            (disease_icd, disease_name, disease_name_norm, treatment_type, drug_name, drug_name_norm, frequency) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            # Use executemany. Since we don't have a unique constraint on JUST ICD (likely), 
            # this might create duplicates if we run multiple times.
            # But the table likely has no unique constraint on these fields alone.
            # We should probably check if it exists first? 
            # Or just DELETE FROM knowledge_base WHERE drug_name = '_ICD_LIST_' before inserting.
            
            cursor.execute("DELETE FROM knowledge_base WHERE drug_name = '_ICD_LIST_'")
            print(f"Deleted {cursor.rowcount} old import rows.")
            
            cursor.executemany(query, rows_to_insert)
            conn.commit()
            print(f"Inserted {cursor.rowcount} rows.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_diseases()
