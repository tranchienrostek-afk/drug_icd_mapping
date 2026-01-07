import csv
import sqlite3
import os
import sys
import unicodedata

# Paths
BASE_DIR = "fastapi-medical-app"
DB_PATH = os.path.join(BASE_DIR, "app/database/medical.db")
CSV_PATH = os.path.join(BASE_DIR, "dulieu_thuoc_playwright.csv")

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    return text.lower().strip()

def run_import():
    print(f"--- Data Reset & Import Tool ---")
    print(f"DB Path: {DB_PATH}")
    print(f"CSV Path: {CSV_PATH}")

    if not os.path.exists(CSV_PATH):
        print("Error: CSV file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Clear Tables
        print("Clearing tables...")
        cursor.execute("DELETE FROM drugs")
        cursor.execute("DELETE FROM drugs_fts")
        cursor.execute("DELETE FROM drug_staging")
        cursor.execute("DELETE FROM drug_staging_history")
        
        # Reset IDs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='drugs'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='drugs_fts'") # Usually no sequence for fts but safe
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='drug_staging'")
        
        conn.commit()
        print("Tables cleared.")

        # 2. Read CSV & Insert
        print("Reading CSV...")
        count = 0
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Map Fields
                sdk = row.get('so_dang_ky', '').strip()
                ten = row.get('ten_thuoc', '').strip()
                hoat_chat = row.get('hoat_chat', '').strip()
                chi_dinh = row.get('noi_dung_dieu_tri', '').strip()
                
                # Check for "Missing" -> Empty string
                # Already handled by .get(..., '').strip()
                
                # Optional fields
                classification = row.get('dang_bao_che', '').strip()
                url = row.get('url_nguon', '').strip()
                note = f"Source: {url}" if url else ""
                
                # Skip if essential info missing? 
                # User said "trường nào thiếu thì để trống", implying we import even if fields are empty.
                # But 'ten_thuoc' is usually required in `drugs` table (NOT NULL check).
                if not ten:
                    print(f"Skipping row with missing 'ten_thuoc': {row}")
                    continue

                # Search Text
                search_text = normalize_text(f"{ten} {hoat_chat} {sdk} {classification}")
                
                # Insert
                cursor.execute("""
                    INSERT INTO drugs (
                        ten_thuoc, so_dang_ky, hoat_chat, chi_dinh, 
                        classification, note, 
                        is_verified, search_text, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'import_script')
                """, (ten, sdk, hoat_chat, chi_dinh, classification, note, search_text))
                
                drug_id = cursor.lastrowid
                
                # FTS
                cursor.execute("""
                    INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)
                    VALUES (?, ?, ?, ?, ?)
                """, (drug_id, ten, hoat_chat, "", search_text))
                
                count += 1
                if count % 100 == 0:
                    print(f"Imported {count} rows...")

        conn.commit()
        print(f"--- SUCCESS: Imported {count} drugs ---")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_import()
