"""
ETL Service for Medical Data Ingestion
=======================================
Handles CSV parsing and loading into knowledge_base table.

Version: 2.0.0
Updated: 2026-01-16
"""

import pandas as pd
import re
import io
import csv
import sqlite3
import os
import logging
from datetime import datetime
from app.core.utils import normalize_drug_name, normalize_text

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "app/database/medical.db")


def normalize_classification(value: str) -> str:
    """
    Normalize classification labels based on Expert Rules (Hierarchy Mapping).
    Returns a JSON string of list, e.g., '["drug", "invalid"]'
    """
    import json
    if not value:
        return json.dumps([])
    
    value = value.lower().strip()
    
    # Remove existing list brackets if present
    value = value.replace('[', '').replace(']', '').replace("'", "").replace('"', "")
    
    # Split by comma if multiple values
    parts = [p.strip() for p in value.split(',') if p.strip()]
    
    # Apply Rules
    # Rule 1: 'supplement' -> ['nodrug', 'supplement']
    if 'supplement' in parts:
        if 'nodrug' not in parts: parts.insert(0, 'nodrug')
        
    # Rule 2: 'medical supplies' -> ['nodrug', 'medical supplies']
    if 'medical supplies' in parts:
        if 'nodrug' not in parts: parts.insert(0, 'nodrug')
        
    # Rule 3: 'cosmeceuticals' -> ['nodrug', 'cosmeceuticals']
    if 'cosmeceuticals' in parts:
        if 'nodrug' not in parts: parts.insert(0, 'nodrug')

    # Rule 4: 'medical equipment' -> ['nodrug', 'medical equipment']
    if 'medical equipment' in parts:
        if 'nodrug' not in parts: parts.insert(0, 'nodrug')
        
    # Rule 5: 'invalid' -> ['drug', 'invalid']
    if 'invalid' in parts:
        if 'drug' not in parts: parts.insert(0, 'drug')
        
    # Rule 6: 'valid' -> ['drug', 'valid', 'main drug'] (Default)
    if 'valid' in parts:
        if 'drug' not in parts: parts.insert(0, 'drug')
        if 'main drug' not in parts and 'secondary drug' not in parts:
            parts.append('main drug')
            
    # Rule 7: 'secondary drug' -> ['drug', 'valid', 'secondary drug']
    if 'secondary drug' in parts:
        if 'drug' not in parts: parts.insert(0, 'drug')
        if 'valid' not in parts: parts.insert(1, 'valid')
        
    # Rule 8: 'drug' alone -> Leave as is (or minimal valid?)
    # Expert said: "If only drug... keep as is"
    
    return json.dumps(list(set(parts))) # Deduplicate and serialize

def parse_icd_field(value: str) -> tuple:
    """
    Parse ICD field format: 'J00 - Viêm mũi họng cấp' into ('j00', 'Viêm mũi họng cấp')
    
    Returns:
        tuple: (icd_code_lowercase, disease_name) or ('', '') if empty
    """
    if not value or not value.strip():
        return ('', '')
    
    value = value.strip()
    
    # Pattern: CODE - Name (e.g., "J00 - Viêm mũi họng" or "B97.4 - Vi rút")
    match = re.match(r'^([A-Z]\d+(?:\.\d+)?)\s*-\s*(.+)$', value, re.IGNORECASE)
    if match:
        icd_code = match.group(1).lower().strip()
        disease_name = match.group(2).strip()
        return (icd_code, disease_name)
    
    # Fallback: return as-is for disease name
    return ('', value)


def parse_secondary_disease_field(value: str) -> tuple:
    """
    Parse secondary disease field which can be in two formats:
    1. Plain text: "B97.4 - Vi rút hợp bào" 
    2. JSON (legacy): '{"uuid": {"id": "...", "ma": "B97.4", "ten": "Vi rút..."}}'
    
    Returns:
        tuple: (icd_code_lowercase, disease_name) or ('', '') if empty
    """
    if not value or not value.strip():
        return ('', '')
    
    value = value.strip()
    
    # Check if it's empty JSON object
    if value == '{}':
        return ('', '')
    
    # Try to parse as JSON first (legacy format)
    if value.startswith('{') and value.endswith('}'):
        try:
            import json
            # Fix escaped quotes from CSV
            clean_value = value.replace('""', '"')
            data = json.loads(clean_value)
            
            if isinstance(data, dict) and data:
                # Get first entry (there might be multiple secondary diseases)
                first_key = list(data.keys())[0]
                entry = data[first_key]
                if isinstance(entry, dict):
                    icd_code = entry.get('ma', '').lower().strip()
                    disease_name = entry.get('ten', '').strip()
                    return (icd_code, disease_name)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    
    # Fall back to plain text format "CODE - Name"
    return parse_icd_field(value)


def lookup_disease_ref_id(cursor, icd_code: str) -> int:
    """
    Lookup disease reference ID from diseases table by ICD code.
    
    Returns:
        int: disease ID or None if not found
    """
    if not icd_code:
        return None
    
    try:
        cursor.execute("""
            SELECT id FROM diseases WHERE LOWER(icd_code) = ?
        """, (icd_code.lower(),))
        row = cursor.fetchone()
        if row:
            return row['id'] if isinstance(row, dict) else row[0]
    except Exception:
        pass
    
    return None


def lookup_drug_ref_id(drug_name: str, search_service=None) -> tuple:
    """
    Lookup drug reference ID from drugs table using fuzzy matching.
    
    Args:
        drug_name: The drug name to search for
        search_service: DrugSearchService instance (optional, creates new if None)
    
    Returns:
        tuple: (drug_id, so_dang_ky, confidence) or (None, None, 0.0)
    """
    if not drug_name or not drug_name.strip():
        return (None, None, 0.0)
    
    try:
        # Lazy import to avoid circular dependency
        if search_service is None:
            from app.database.core import DatabaseCore
            from app.service.drug_search_service import DrugSearchService
            db_core = DatabaseCore(DB_PATH)
            search_service = DrugSearchService(db_core)
        
        # Use sync wrapper for async search
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context, use nest_asyncio or thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, search_service.search_drug_smart(drug_name))
                    result = future.result(timeout=5)
            else:
                result = loop.run_until_complete(search_service.search_drug_smart(drug_name))
        except RuntimeError:
            # No event loop, create new one
            result = asyncio.run(search_service.search_drug_smart(drug_name))
        
        if result and result.get('confidence', 0) >= 0.85:
            data = result.get('data', {})
            drug_id = data.get('rowid') or data.get('id')
            sdk = data.get('so_dang_ky', '')
            confidence = result.get('confidence', 0.0)
            logger.debug(f"[ETL] Drug matched: '{drug_name}' -> ID={drug_id}, SDK={sdk}, Conf={confidence:.2f}")
            return (drug_id, sdk, confidence)
            
    except Exception as e:
        logger.warning(f"[ETL] Drug lookup failed for '{drug_name}': {e}")
    
    return (None, None, 0.0)


def process_raw_log(batch_id: str, text_content: str) -> dict:
    """
    Process raw CSV log ingestion for Knowledge Base building.
    Pre-lookups drug IDs to avoid DB locking, then does batch insertion.
    
    Expected CSV columns:
    - Tên thuốc (required)
    - Mã ICD (Chính) (required)
    - ...
    """
    logger.info(f"[ETL] Starting process_raw_log for batch: {batch_id}")
    
    # Initialize stats
    stats = {
        "batch_id": batch_id,
        "total_rows": 0,
        "inserted": 0,
        "updated": 0,
        "errors": 0,
        "drugs_matched": 0,
        "diseases_matched": 0
    }
    
    try:
        # FIX: Write directly to main DB instead of temp DB copy (which overwrites all data)
        import shutil
        import uuid
        import os
        
        # No longer using temp DB - write directly to main
        
        # 1. Parse CSV
        reader = csv.DictReader(io.StringIO(text_content))
        rows = list(reader)
        stats["total_rows"] = len(rows)
        logger.info(f"[ETL] Parsed {len(rows)} rows from CSV")
        print(f"[ETL] === PHASE 1: Parsed {len(rows)} rows from CSV ===", flush=True)
        
        if not rows:
            return stats

        # 2. Identify Unique Drugs and Pre-lookup (READ PHASE)
        # DISABLED: Skip drug lookup for now to ensure basic ETL works
        # Drug mapping can be enabled later once basic functionality is stable
        batch_map = {}
        print(f"[ETL] === PHASE 2: SKIPPED (drug lookup disabled for speed) ===", flush=True)
        
        # PHASE 2 DISABLED - Original code commented out:
        # unique_drugs = set()
        # for row in rows:
        #     dn = (row.get('Tên thuốc', '') or row.get('ten_thuoc', '') or '').strip()
        #     if dn: unique_drugs.add(dn)
        # from app.database.core import DatabaseCore
        # from app.service.drug_search_service import DrugSearchService
        # db_core = DatabaseCore(DB_PATH)
        # search_service = DrugSearchService(db_core)
        # import asyncio
        # for drug in unique_drugs:
        #     try: ... lookup logic ...
        #     except: pass

        # 5. WRITE TO TEMP DB (WRITE PHASE)

        # Connect to MAIN DB for Lookups (Read-Only)
        conn_main = sqlite3.connect(DB_PATH)
        conn_main.row_factory = sqlite3.Row
        cursor_main = conn_main.cursor()

        # 5. WRITE DIRECTLY TO MAIN DB (FIX: No more temp DB copy)
        # Now we write directly to main DB with proper locking
        conn = sqlite3.connect(DB_PATH, timeout=60.0)
        conn.execute("PRAGMA journal_mode=DELETE;")  # Avoid WAL issues on Windows
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Explicitly Create Base Table in Temp DB
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_name TEXT,
                drug_name_norm TEXT,
                drug_ref_id INTEGER,
                disease_icd TEXT,
                disease_name TEXT,
                disease_name_norm TEXT,
                disease_ref_id INTEGER,
                secondary_disease_icd TEXT,
                secondary_disease_name TEXT,
                secondary_disease_name_norm TEXT,
                secondary_disease_ref_id INTEGER,
                treatment_type TEXT,
                tdv_feedback TEXT,
                symptom TEXT,
                prescription_reason TEXT,
                frequency INTEGER DEFAULT 1,
                confidence_score REAL DEFAULT 0.0,
                batch_id TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        _ensure_kb_columns(cursor)
        conn.commit()
        
        # Process Rows Logic (Same as before)
        print(f"[ETL] === PHASE 3: Processing {len(rows)} rows ===", flush=True)
        processed_count = 0
        for row in rows:
            try:
                 # === DRUG INFO ===
                # Handle various column name formats from different CSV sources
                # User Request (2026-01-20): Map '?column?' to thuoc_chinh (Drug Name)
                drug_name = (row.get('Tên thuốc', '') or row.get('ten_thuoc', '') or row.get('Ten_thuoc', '') or row.get('?column?', '') or row.get('thuoc_chinh', '') or '').strip()
                if not drug_name:
                    stats["errors"] += 1
                    continue
                drug_name_norm = normalize_text(drug_name)
                
                drug_ref_id, drug_sdk, drug_conf = batch_map.get(drug_name, (None, None, 0.0))
                if drug_ref_id: stats["drugs_matched"] += 1
                
                # === PRIMARY DISEASE ===
                primary_icd_raw = (row.get('Mã ICD (Chính)', '') or row.get('benh_chinh', '') or '').strip()
                if not primary_icd_raw:
                    stats["errors"] += 1
                    continue
                disease_icd, disease_name = parse_icd_field(primary_icd_raw)
                disease_ref_id = lookup_disease_ref_id(cursor_main, disease_icd)
                if disease_ref_id: stats["diseases_matched"] += 1
                
                # === SECONDARY ===
                # Handle case variations: Benh_phu, benh_phu, Bệnh phụ
                secondary_raw = (row.get('Bệnh phụ', '') or row.get('benh_phu', '') or row.get('Benh_phu', '') or '').strip()
                secondary_icd, secondary_name = parse_secondary_disease_field(secondary_raw)
                secondary_name_norm = normalize_text(secondary_name) if secondary_name else ''
                secondary_ref_id = lookup_disease_ref_id(cursor_main, secondary_icd)
                
                
                 # === OTHER FIELDS ===
                treatment_type_raw = (row.get('Phân loại', '') or row.get('phan_loai', '') or '').strip()
                treatment_type = normalize_classification(treatment_type_raw)
                
                tdv_feedback_raw = (row.get('Feedback', '') or row.get('tdv_feedback', '') or '').strip()
                # Apply normalization to tdv_feedback too if it contains classification tags
                tdv_feedback = normalize_classification(tdv_feedback_raw)
                symptom = (row.get('Chẩn đoán ra viện', '') or row.get('chuan_doan_ra_vien', '') or '').strip()
                # Handle Ly_do with capital L
                prescription_reason = (row.get('Lý do kê đơn', '') or row.get('ly_do', '') or row.get('Ly_do', '') or '').strip()

                # === UPSERT ===
                cursor.execute("SELECT id, frequency FROM knowledge_base WHERE drug_name_norm = ? AND disease_icd = ?", (drug_name_norm, disease_icd))
                existing = cursor.fetchone()
                
                if existing:
                    new_freq = (existing['frequency'] or 0) + 1
                    cursor.execute("""
                        UPDATE knowledge_base 
                        SET frequency = ?, drug_ref_id = COALESCE(?, drug_ref_id),
                            treatment_type = COALESCE(?, treatment_type),
                            tdv_feedback = COALESCE(?, tdv_feedback),
                            symptom = COALESCE(?, symptom),
                            prescription_reason = COALESCE(?, prescription_reason),
                            last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_freq, drug_ref_id, treatment_type or None, tdv_feedback or None, symptom or None, prescription_reason or None, existing['id']))
                    stats["updated"] += 1
                else:
                    cursor.execute("""
                        INSERT INTO knowledge_base 
                        (drug_name, drug_name_norm, drug_ref_id,
                         disease_icd, disease_name, disease_name_norm, disease_ref_id,
                         secondary_disease_icd, secondary_disease_name, secondary_disease_name_norm, secondary_disease_ref_id,
                         treatment_type, tdv_feedback, symptom, prescription_reason,
                         frequency, batch_id, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                    """, (drug_name, drug_name_norm, drug_ref_id, disease_icd, disease_name, normalize_text(disease_name) if disease_name else '', disease_ref_id,
                          secondary_icd, secondary_name, secondary_name_norm, secondary_ref_id,
                          treatment_type, tdv_feedback, symptom, prescription_reason, batch_id))
                    stats["inserted"] += 1
                
                # Progress logging every 100 rows
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"[ETL] Progress: {processed_count}/{len(rows)} rows processed...", flush=True)
                    
            except Exception as row_e:
                stats["errors"] += 1
        
        conn.commit()
        conn.close() 
        try: conn_main.close()
        except: pass
        
        # FIX: No longer copying temp DB - data is already in main DB
        print(f"[ETL] Batch {batch_id} written directly to main DB.", flush=True)
        
        logger.info(f"[ETL] Batch {batch_id} complete: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"[ETL] Fatal error processing batch {batch_id}: {e}")
        raise



def _ensure_kb_columns(cursor):
    """
    Ensure knowledge_base has all required columns (migration helper).
    """
    # Get existing columns
    cursor.execute("PRAGMA table_info(knowledge_base)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    # Define new columns to add
    new_columns = [
        ("drug_name", "TEXT"),
        ("secondary_disease_icd", "TEXT"),
        ("secondary_disease_name", "TEXT"),
        ("secondary_disease_name_norm", "TEXT"),
        ("secondary_disease_ref_id", "INTEGER"),
        ("symptom", "TEXT"),
        ("prescription_reason", "TEXT"),
        ("batch_id", "TEXT"),
        ("tdv_feedback", "TEXT"), # Added v2.1
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE knowledge_base ADD COLUMN {col_name} {col_type}")
                logger.info(f"[ETL Migration] Added column: {col_name}")
            except Exception as e:
                logger.warning(f"[ETL Migration] Column {col_name} may already exist: {e}")


# ============================================================================
# LEGACY CLASS (kept for backward compatibility)
# ============================================================================

class EtlService:
    def __init__(self):
        pass

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load CSV data safely."""
        try:
            df = pd.read_csv(file_path, on_bad_lines='skip')
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            raise

    def clean_and_deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean whitespace and deduplicate based on 'so_dang_ky'."""
        if df.empty:
            return df
            
        initial_count = len(df)
        df.columns = df.columns.str.strip()
        
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            
        if 'so_dang_ky' in df.columns:
            df['completeness_score'] = df.apply(
                lambda row: sum(1 for x in row if x and str(x).lower() != 'nan' and str(x).strip() != ''), 
                axis=1
            )
            df = df.sort_values(by=['so_dang_ky', 'completeness_score'], ascending=[True, False])
            df = df.drop_duplicates(subset=['so_dang_ky'], keep='first')
            df = df.drop(columns=['completeness_score'])
            
        final_count = len(df)
        logger.info(f"Deduplication: Removed {initial_count - final_count} duplicate rows.")
        
        return df

    def extract_info_from_description(self, text: str) -> dict:
        """Extract 'chi_dinh' and 'chong_chi_dinh' from 'noi_dung_dieu_tri'."""
        if not isinstance(text, str) or not text or text.lower() == 'nan':
            return {"chi_dinh": None, "chong_chi_dinh": None}
        return {"chi_dinh": text, "chong_chi_dinh": None}

    def process_for_import(self, df: pd.DataFrame) -> list:
        """Convert DataFrame to list of dicts ready for DB import."""
        records = []
        for _, row in df.iterrows():
            record = {
                "so_dang_ky": row.get('so_dang_ky'),
                "ten_thuoc": row.get('ten_thuoc'),
                "hoat_chat": row.get('hoat_chat'),
                "dang_bao_che": row.get('dang_bao_che'),
                "nong_do": row.get('ham_luong'),
                "nhom_thuoc": row.get('danh_muc'),
                "source_urls": [row.get('url_nguon')] if row.get('url_nguon') else [],
                "source": "ThuocBietDuoc Crawler (Import)"
            }
            extracted = self.extract_info_from_description(row.get('noi_dung_dieu_tri'))
            record['chi_dinh'] = extracted['chi_dinh']
            record['chong_chi_dinh'] = extracted['chong_chi_dinh']
            cleaned_record = {k: v for k, v in record.items() if v and str(v).lower() != 'nan'}
            records.append(cleaned_record)
        return records
