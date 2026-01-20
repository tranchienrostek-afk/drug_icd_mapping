import sqlite3
import csv
import os
import glob
import sys
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "app/database/medical.db")
DATACORE_DIR = r"C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\datacore_thuocbietduoc"

def normalize_text(text):
    if not text: return ""
    return str(text).strip()

def run_import():
    print(f"--- Import Drugs Master from Datacore ---")
    print(f"DB: {DB_PATH}")
    print(f"Source Dir: {DATACORE_DIR}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Recreate Tables (Strict Spec 01_drugs_master.md)
        print("Recreating tables `drugs`, `drug_staging`, `drugs_fts`...")
        
        # Table: drugs
        cursor.execute("DROP TABLE IF EXISTS drugs")
        cursor.execute("""
            CREATE TABLE drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_thuoc TEXT,
                so_dang_ky TEXT,
                hoat_chat TEXT,
                cong_ty_san_xuat TEXT,
                chi_dinh TEXT,
                tu_dong_nghia TEXT,
                classification TEXT,
                note TEXT,
                is_verified INTEGER DEFAULT 1,
                search_text TEXT,
                created_by TEXT,
                created_at TIMESTAMP,
                updated_by TEXT,
                updated_at TIMESTAMP
            )
        """)

        # Table: drug_staging
        cursor.execute("DROP TABLE IF EXISTS drug_staging")
        cursor.execute("""
            CREATE TABLE drug_staging (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_thuoc TEXT,
                so_dang_ky TEXT,
                hoat_chat TEXT,
                cong_ty_san_xuat TEXT,
                chi_dinh TEXT,
                tu_dong_nghia TEXT,
                search_text TEXT,
                status TEXT DEFAULT 'pending',
                conflict_type TEXT,
                conflict_id INTEGER,
                classification TEXT,
                note TEXT,
                created_by TEXT,
                created_at TIMESTAMP
            )
        """)

        # Table: drugs_fts
        cursor.execute("DROP TABLE IF EXISTS drugs_fts")
        cursor.execute("""
            CREATE VIRTUAL TABLE drugs_fts USING fts5(
                ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text,
                content='drugs', content_rowid='id'
            )
        """)
        
        conn.commit()

        # 2. Import Data from CSVs
        csv_files = glob.glob(os.path.join(DATACORE_DIR, "*.csv"))
        print(f"Found {len(csv_files)} CSV files.")
        
        total_imported = 0
        total_error = 0
        
        for csv_file in csv_files:
            print(f"Processing {os.path.basename(csv_file)}...")
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Check headers
                # We expect: so_dang_ky, ten_thuoc, hoat_chat, ...
                
                for row in reader:
                    try:
                        # Extract & Map
                        ten_thuoc = normalize_text(row.get('ten_thuoc', ''))
                        so_dang_ky = normalize_text(row.get('so_dang_ky', ''))
                        hoat_chat = normalize_text(row.get('hoat_chat', ''))
                        chi_dinh = normalize_text(row.get('noi_dung_dieu_tri', '')) # Map from noi_dung_dieu_tri
                        
                        # Optional fields
                        classification = normalize_text(row.get('dang_bao_che', ''))
                        cong_ty_san_xuat = "" # Not in CSV explicit columns usually, or blank
                        
                        # Note construction
                        note_parts = []
                        danh_muc = normalize_text(row.get('danh_muc', ''))
                        url_nguon = normalize_text(row.get('url_nguon', ''))
                        if danh_muc: note_parts.append(f"Danh mục: {danh_muc}")
                        if url_nguon: note_parts.append(f"Source: {url_nguon}")
                        note = "; ".join(note_parts)
                        
                        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Search Text
                        search_text = f"{ten_thuoc} {hoat_chat} {so_dang_ky} {classification}".lower().strip()
                        
                        # Insert
                        cursor.execute("""
                            INSERT INTO drugs (
                                ten_thuoc, so_dang_ky, hoat_chat, cong_ty_san_xuat,
                                chi_dinh, classification, note, is_verified,
                                search_text, created_by, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'import_script', ?, ?)
                        """, (
                            ten_thuoc, so_dang_ky, hoat_chat, cong_ty_san_xuat,
                            chi_dinh, classification, note, search_text, created_at, created_at
                        ))
                        
                        drug_id = cursor.lastrowid
                        
                        # FTS Insert
                        cursor.execute("""
                            INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)
                            VALUES (?, ?, ?, ?, ?)
                        """, (drug_id, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text))

                        total_imported += 1
                        
                    except Exception as row_err:
                        # print(f"Row Error: {row_err}")
                        total_error += 1
                        
        conn.commit()
        print(f"\n✅ SUCCESS: Imported {total_imported} drugs.")
        print(f"❌ Errors: {total_error}")

    except Exception as e:
        print(f"❌ Script Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_import()
