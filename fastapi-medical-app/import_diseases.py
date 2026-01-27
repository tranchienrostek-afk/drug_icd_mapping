
import sys
import os
import csv
import logging
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

INPUT_FILE = "import_data/icd_data.csv"

import asyncio
import time

def import_diseases():
    db = DatabaseCore()
    conn = db.get_connection()
    
    # Optimize for bulk import
    try:
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute("PRAGMA journal_mode = MEMORY")
        conn.execute("PRAGMA cache_size = 100000")
        conn.execute("PRAGMA locking_mode = EXCLUSIVE")
    except Exception as e:
        logger.warning(f"Could not set optimization pragmas: {e}")

    cursor = conn.cursor()
    
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        return

    logger.info("Starting ICD import...")
    
    try:
        logger.info("Truncating current diseases table...")
        cursor.execute("DELETE FROM diseases")
        conn.commit()

        with open(INPUT_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            
            batch_size = 500 # Reduced batch size
            batch = []
            count = 0
            
            for row in reader:
                if not row: continue 
                
                try:
                    record_id = row[0].strip()
                    icd_code = row[10].strip()
                    chapter_name = row[14].strip() if len(row) > 14 else ""
                    slug = row[15].strip() if len(row) > 15 else ""
                    disease_name = row[16].strip() if len(row) > 16 else ""
                    
                    if not icd_code or not disease_name:
                        continue 
                        
                    search_text = f"{icd_code} {disease_name} {slug} {chapter_name}".strip().lower()
                    
                    batch.append((
                        record_id,
                        icd_code,
                        disease_name,
                        chapter_name,
                        slug,
                        search_text,
                        'active'
                    ))
                    
                    if len(batch) >= batch_size:
                        _execute_batch_safe(conn, cursor, batch)
                        count += len(batch)
                        batch = []
                        
                except IndexError:
                    logger.warning(f"Skipping malformed row: {row}")
                    continue
            
            if batch:
                _execute_batch_safe(conn, cursor, batch)
                count += len(batch)
                
            logger.info(f"✅ Finished importing {count} records.")
            with open("import_result.txt", "w") as rf:
                rf.write(str(count))
            
            logger.info("Updating FTS index...")
            cursor.execute("DELETE FROM diseases_fts")
            cursor.execute("INSERT INTO diseases_fts(icd_code, disease_name, search_text) SELECT icd_code, disease_name, search_text FROM diseases")
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
                INSERT OR IGNORE INTO diseases (
                    id, icd_code, disease_name, chapter_name, slug, search_text, is_active
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?
                )
            """, batch)
            conn.commit()
            return
        except Exception as e:
            if "disk I/O error" in str(e) or "database is locked" in str(e):
                logging.warning(f"Batch failed (attempt {attempt+1}/{retries}): {e}. Retrying...")
                time.sleep(1)
            else:
                raise e
    raise RuntimeError("Failed to insert batch after retries")

if __name__ == "__main__":
    import_diseases()
