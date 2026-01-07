import sqlite3
import os

DB_PATH = "app/database/medical.db"

def cleanup_na_drugs():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Find records to delete
        print("Searching for drugs with invalid names ('NA', 'N/A', '', NULL)...")
        cursor.execute("SELECT rowid, so_dang_ky FROM drugs WHERE ten_thuoc IN ('NA', 'N/A', '') OR ten_thuoc IS NULL")
        rows = cursor.fetchall()
        
        if not rows:
            print("No 'NA' drugs found.")
            return

        row_ids = [r[0] for r in rows]
        sdks = [r[1] for r in rows if r[1]]
        count = len(row_ids)
        print(f"Found {count} records to delete.")

        # 2. Delete from FTS
        sql_fts = f"DELETE FROM drugs_fts WHERE rowid IN ({','.join(['?']*len(row_ids))})"
        cursor.execute(sql_fts, row_ids)
        print("Deleted from FTS.")

        # 3. Delete from Main Table
        sql_main = f"DELETE FROM drugs WHERE rowid IN ({','.join(['?']*len(row_ids))})"
        cursor.execute(sql_main, row_ids)
        print("Deleted from drugs table.")

        # 4. Optional: Delete from Links if any
        if sdks:
            sql_links = f"DELETE FROM drug_disease_links WHERE sdk IN ({','.join(['?']*len(sdks))})"
            cursor.execute(sql_links, sdks)
            print("Deleted from drug_disease_links.")

        conn.commit()
        print("Cleanup successful!")

    except sqlite3.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_na_drugs()
