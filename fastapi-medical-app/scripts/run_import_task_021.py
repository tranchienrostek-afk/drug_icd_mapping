import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, r'C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app')

from app.service.etl_service import EtlService

CSV_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\ketqua_thuoc_part_20260107_154800.csv"
DB_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\app\database\medical.db"

def run_import():
    print("="*60)
    print("TASK 021 - IMPORT & DEDUPLICATE DRUG DATA")
    print("="*60)
    
    # 1. Pipeline: Load -> Clean -> Deduplicate
    etl_service = EtlService()
    
    print("\n[Step 1] Loading and Cleaning Data...")
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV File not found: {CSV_PATH}")
        return

    df = etl_service.load_csv(CSV_PATH)
    df_clean = etl_service.clean_and_deduplicate(df)
    
    records = etl_service.process_for_import(df_clean)
    print(f"✅ Ready to import {len(records)} unique records.")
    
    # 2. Database Import (Smart Upsert)
    print("\n[Step 2] Importing to Database (Smart Upsert)...")
    if not os.path.exists(DB_PATH):
        print(f"❌ DB File not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- Auto Migration for TASK 021 ---
    try:
        cursor.execute("SELECT source_urls FROM drugs LIMIT 1")
    except sqlite3.OperationalError:
        print("⚠️ Migrating DB: Adding 'source_urls' column...")
        cursor.execute("ALTER TABLE drugs ADD COLUMN source_urls TEXT")
        conn.commit()
    # -----------------------------------
    
    stats = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    try:
        for rec in records:
            sdk = rec.get('so_dang_ky')
            if not sdk:
                stats['skipped'] += 1
                continue
                
            ten = rec.get('ten_thuoc', '')
            hoat_chat = rec.get('hoat_chat', '')
            chi_dinh = rec.get('chi_dinh', '')
            # Map other fields
            cong_ty = "" # CSV doesn't have this explicitly? Or maybe in diff column?
            # 'dang_bao_che', 'nong_do' -> can be appended to hoat_chat or note/classification
            dang_bao_che = rec.get('dang_bao_che', '')
            nong_do = rec.get('nong_do', '')
            
            # Enhancing hoat_chat or note with extra info
            full_hoat_chat = hoat_chat
            if nong_do and nong_do not in hoat_chat:
                full_hoat_chat = f"{hoat_chat} {nong_do}".strip()
                
            note = f"Bào chế: {dang_bao_che}" if dang_bao_che else ""
            nhom = rec.get('nhom_thuoc', '')
            if nhom:
                if note: note += f"; Nhóm: {nhom}"
                else: note = f"Nhóm: {nhom}"
                
            source_url = rec.get('source_urls', [])
            source_url_str = source_url[0] if source_url else ""
            
            # --- Upsert Logic ---
            # Check exist by SDK
            cursor.execute("SELECT rowid, ten_thuoc, chi_dinh, note, source_urls FROM drugs WHERE so_dang_ky = ?", (sdk,))
            row = cursor.fetchone()
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = "import_task_021"
            
            if row:
                # Exists -> Update Missing Info
                row_id = row[0]
                current_chi_dinh = row[2]
                current_note = row[3]
                
                updates = []
                params = []
                
                # Update chi_dinh if missing
                if not current_chi_dinh and chi_dinh:
                    updates.append("chi_dinh = ?")
                    params.append(chi_dinh)
                    
                # Update note (append if possible, or fill)
                if not current_note and note:
                    updates.append("note = ?")
                    params.append(note)
                
                # Update source_urls if missing
                current_source = row[4] if len(row) > 4 else None
                if not current_source and source_url_str:
                    updates.append("source_urls = ?")
                    params.append(source_url_str)

                if updates:
                    updates.append("updated_by = ?")
                    updates.append("updated_at = ?")
                    params.append(user)
                    params.append(now)
                    params.append(row_id) # WHERE clause
                    
                    sql = f"UPDATE drugs SET {', '.join(updates)} WHERE rowid = ?"
                    cursor.execute(sql, params)
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
            else:
                # New -> Insert
                search_text = f"{ten} {full_hoat_chat} {sdk}".lower()
                
                sql_insert = """
                    INSERT INTO drugs (
                        ten_thuoc, hoat_chat, so_dang_ky, chi_dinh, 
                        is_verified, search_text, created_by, created_at, updated_at,
                        note, classification, source_urls
                    ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql_insert, (
                    ten, full_hoat_chat, sdk, chi_dinh, 
                    search_text, user, now, now,
                    note, nhom, source_url_str
                ))
                stats['inserted'] += 1
                
        conn.commit()
        print("\n✅ Import Completed Successfully!")
        print(f"  - Inserted: {stats['inserted']}")
        print(f"  - Updated (enriched): {stats['updated']}")
        print(f"  - Skipped (no changes/no SDK): {stats['skipped']}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during import: {e}")
    finally:
        conn.close()

    print("\n" + "="*60)

if __name__ == "__main__":
    run_import()
