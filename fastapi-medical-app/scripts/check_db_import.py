import sqlite3
import pandas as pd

DB_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\app\database\medical.db"

def verify():
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get count
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM drugs")
        total = cursor.fetchone()[0]
        print(f"Total Drugs in DB: {total}")
        
        # Get latest 5
        print("\nLatest 5 inserted drugs:")
        df = pd.read_sql_query("SELECT ten_thuoc, so_dang_ky, hoat_chat, created_at, source_urls FROM drugs ORDER BY created_at DESC LIMIT 5", conn)
        print(df.to_string())
        
        # Verify source_urls
        print("\nVerify source_urls content:")
        cursor.execute("SELECT source_urls FROM drugs WHERE source_urls IS NOT NULL LIMIT 1")
        print(cursor.fetchone())
        
        print(f"\n✅ FINAL CHECK - Total Drugs in DB: {total}")

        
    finally:
        conn.close()

if __name__ == "__main__":
    verify()
