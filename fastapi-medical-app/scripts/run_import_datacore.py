import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime
import glob

# Add project root to path
sys.path.insert(0, r'C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app')

from app.data_refinery import DataRefinery
from app.utils import normalize_text

DATACORE_DIR = r"C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\datacore_thuocbietduoc"
DB_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\app\database\medical.db"

def run_import_datacore():
    print("="*60)
    print("TASK 022 - IMPORT DATACORE (FULL MERGE)")
    print("="*60)
    
    refinery = DataRefinery()
    
    # [Step 1] Load All CSVs
    print("\n[Step 1] Loading all CSV files from DataCore...")
    csv_files = glob.glob(os.path.join(DATACORE_DIR, "*.csv"))
    
    if not csv_files:
        print("❌ No CSV files found!")
        return
        
    df_list = []
    total_raw_rows = 0
    
    for f in csv_files:
        try:
            print(f"  - Reading {os.path.basename(f)} ...", end=" ")
            # Read header first to check format compatibility? 
            # Assuming all have same format derived from scrapper_data_drugs.py
            df = pd.read_csv(f, on_bad_lines='skip', dtype=str) # Read as str to avoid checking types
            print(f"Rows: {len(df)}")
            df_list.append(df)
            total_raw_rows += len(df)
        except Exception as e:
            print(f"❌ Error: {e}")
            
    if not df_list:
        print("❌ No valid data loaded.")
        return

    print(f"\n📊 Total Raw Rows: {total_raw_rows}")
    
    full_df = pd.concat(df_list, ignore_index=True)
    
    # [Step 2] Clean & Deduplicate
    print("\n[Step 2] Cleaning and Deduplicating...")
    df_clean = refinery.clean_and_deduplicate(full_df)
    
    records = refinery.process_for_import(df_clean)
    print(f"✅ Ready to import {len(records)} unique records.")
    
    # [Step 3] Database Import
    print("\n[Step 3] Importing to Database...")
    if not os.path.exists(DB_PATH):
        print(f"❌ DB File not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Auto Migration (ensure)
    try:
        cursor.execute("SELECT source_urls FROM drugs LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE drugs ADD COLUMN source_urls TEXT")
        conn.commit()
    
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = "import_task_022_datacore"

    try:
        # Optimization: Pre-load existing SDKs into a set for faster checking?
        # But we need rowid and existing data to decide update.
        # So selection is still needed. We can SELECT all relevant columns into a Dictionary in memory.
        # Dictionary: sdk -> {rowid, chi_dinh, note, source_urls}
        # This reduces 20k SELECT queries to 1 SELECT query.
        
        print("  - Pre-loading existing DB index...")
        cursor.execute("SELECT rowid, so_dang_ky, chi_dinh, note, source_urls FROM drugs WHERE so_dang_ky IS NOT NULL")
        db_cache = {}
        for row in cursor.fetchall():
            # row[1] is sdk. dict_factory might be active? 
            # Default cursor in script does NOT use dict_factory unless set.
            # checking simple script: no row_factory set. So tuples.
            # 0:rowid, 1:sdk, 2:chi_dinh, 3:note, 4:source_urls
            sdk_key = str(row[1]).strip()
            db_cache[sdk_key] = {
                "rowid": row[0],
                "chi_dinh": row[2],
                "note": row[3],
                "source_urls": row[4]
            }
            
        print(f"  - DB Cache loaded: {len(db_cache)} existing drugs.")
        
        for rec in records:
            sdk = rec.get('so_dang_ky')
            if not sdk:
                stats['skipped'] += 1
                continue
            
            # Normalize SDK to match cache key
            sdk_key = str(sdk).strip()
            
            ten = rec.get('ten_thuoc', '')
            hoat_chat = rec.get('hoat_chat', '')
            chi_dinh = rec.get('chi_dinh', '')
            dang_bao_che = rec.get('dang_bao_che', '')
            nong_do = rec.get('nong_do', '')
            nhom = rec.get('nhom_thuoc', '')

            full_hoat_chat = hoat_chat
            if nong_do and nong_do not in hoat_chat:
                full_hoat_chat = f"{hoat_chat} {nong_do}".strip()
                
            note_parts = []
            if dang_bao_che: note_parts.append(f"Bào chế: {dang_bao_che}")
            if nhom: note_parts.append(f"Nhóm: {nhom}")
            note = "; ".join(note_parts)
            
            source_url = rec.get('source_urls', [])
            source_url_str = source_url[0] if source_url else ""
            
            # CHECK CACHE
            existing = db_cache.get(sdk_key)
            
            if existing:
                # Update Logic
                row_id = existing['rowid']
                current_chi_dinh = existing['chi_dinh']
                current_note = existing['note']
                current_source = existing['source_urls']
                
                updates = []
                params = []
                
                # FIX: Always update search_text with correct normalization
                new_search_text = normalize_text(f"{ten} {full_hoat_chat}")
                updates.append("search_text = ?")
                params.append(new_search_text)
                
                if not current_chi_dinh and chi_dinh:
                    updates.append("chi_dinh = ?")
                    params.append(chi_dinh)
                    
                if not current_note and note:
                    updates.append("note = ?")
                    params.append(note)
                    
                if not current_source and source_url_str:
                    updates.append("source_urls = ?")
                    params.append(source_url_str)

                if updates:
                    updates.append("updated_by = ?")
                    updates.append("updated_at = ?")
                    params.append(user)
                    params.append(now)
                    params.append(row_id)
                    
                    sql = f"UPDATE drugs SET {', '.join(updates)} WHERE rowid = ?"
                    cursor.execute(sql, params)
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
            else:
                # Insert Logic
                search_text = normalize_text(f"{ten} {full_hoat_chat}")
                
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
        print("\n✅ Import Operations Completed!")
        print(f"  - Inserted (New): {stats['inserted']}")
        print(f"  - Updated (Enriched): {stats['updated']}")
        print(f"  - Skipped (No change): {stats['skipped']}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during import: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_import_datacore()
