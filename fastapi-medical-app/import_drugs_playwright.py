
import sys
import os
import csv
import logging
import asyncio
from datetime import datetime

# Setup path to import app modules
sys.path.append(os.getcwd())

from app.database.core import DatabaseCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

INPUT_DIR = "import_data"

def import_drugs():
    db = DatabaseCore()
    conn = db.get_connection()
    
    # Optimize for bulk import
    try:
        conn.execute("PRAGMA synchronous = OFF") # Risky but fast, helps with IO bottlenecks
        conn.execute("PRAGMA journal_mode = MEMORY") # Avoid disk churn for journal
        conn.execute("PRAGMA cache_size = 100000")
        conn.execute("PRAGMA locking_mode = EXCLUSIVE") # Hold lock, good for single writer
    except Exception as e:
        logger.warning(f"Could not set optimization pragmas: {e}")

    cursor = conn.cursor()
    
    if not os.path.exists(INPUT_DIR):
        logger.error(f"Input directory not found: {INPUT_DIR}")
        return

    logger.info(f"Starting import from {INPUT_DIR}...")
    
    seen_records = set()
    
    try:
        logger.info("Truncating current drugs table...")
        cursor.execute("DELETE FROM drugs")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='drugs'")
        conn.commit()

        files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.csv')]
        logger.info(f"Found {len(files)} CSV files: {files}")

        total_imported = 0

        for filename in files:
            file_path = os.path.join(INPUT_DIR, filename)
            logger.info(f"Processing {filename}...")
            
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                batch_size = 500 # Reduced batch size
                batch = []
                file_count = 0
                
                for row in reader:
                    ten_thuoc = row.get('ten_thuoc', '').strip()
                    so_dang_ky = row.get('so_dang_ky', '').strip()
                    hoat_chat = row.get('hoat_chat', '').strip()
                    
                    unique_key = (so_dang_ky, ten_thuoc)
                    if unique_key in seen_records:
                        continue
                    seen_records.add(unique_key)

                    chi_dinh = row.get('noi_dung_dieu_tri', '').strip()
                    classification = row.get('dang_bao_che', '').strip() 
                    
                    url = row.get('url_nguon', '')
                    danh_muc = row.get('danh_muc', '')
                    ham_luong = row.get('ham_luong', '')
                    
                    note_parts = []
                    if danh_muc: note_parts.append(f"Group: {danh_muc}")
                    if ham_luong: note_parts.append(f"Strength: {ham_luong}")
                    if url: note_parts.append(f"Source: {url}")
                    note = " | ".join(note_parts)
                    
                    search_text = f"{ten_thuoc} {hoat_chat} {so_dang_ky} {danh_muc}".strip().lower()
                    
                    batch.append((
                        ten_thuoc,
                        hoat_chat,
                        '', 
                        so_dang_ky,
                        chi_dinh,
                        '', 
                        0, 
                        search_text,
                        'system_import_full',
                        classification,
                        note
                    ))
                    
                    if len(batch) >= batch_size:
                        _execute_batch_safe(conn, cursor, batch)
                        file_count += len(batch)
                        total_imported += len(batch)
                        batch = []
                        # time.sleep(0.01) # Yield to OS
                
                if batch:
                    _execute_batch_safe(conn, cursor, batch)
                    file_count += len(batch)
                    total_imported += len(batch)
                    
            logger.info(f"   -> Imported {file_count} unique records from {filename}")
        
        logger.info(f"✅ Finished importing TOTAL {total_imported} unique records.")
        
        logger.info("Updating FTS index...")
        cursor.execute("DELETE FROM drugs_fts")
        cursor.execute("INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text) SELECT id, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text FROM drugs")
        conn.commit()
        logger.info("FTS Updated.")
            
    except Exception as e:
        logger.error(f"Error during import: {e}")
        conn.rollback()
    finally:
        conn.close()

def _execute_batch_safe(conn, cursor, batch):
    retries = 3
    for attempt in range(retries):
        try:
            cursor.executemany("""
                INSERT INTO drugs (
                    ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, chi_dinh, 
                    tu_dong_nghia, is_verified, search_text, created_by,
                    classification, note, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?,
                    ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """, batch)
            conn.commit()
            return
        except Exception as e:
            if "disk I/O error" in str(e) or "database is locked" in str(e):
                logging.warning(f"Batch failed (attempt {attempt+1}/{retries}): {e}. Retrying...")
                asyncio.sleep(1) # Using asyncio.sleep in sync function won't work, use time.sleep
                import time
                time.sleep(1)
            else:
                raise e
    raise RuntimeError("Failed to insert batch after retries")

def _insert_batch(cursor, batch):
    cursor.executemany("""
        INSERT INTO drugs (
            ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, chi_dinh, 
            tu_dong_nghia, is_verified, search_text, created_by,
            classification, note, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, 
            ?, ?, ?, ?,
            ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
    """, batch)

if __name__ == "__main__":
    import_drugs()
