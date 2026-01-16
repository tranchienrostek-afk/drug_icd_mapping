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


def process_raw_log(batch_id: str, text_content: str):
    """
    Process raw CSV log ingestion for Knowledge Base building.
    
    Expected CSV columns:
    - Tên thuốc (required)
    - Mã ICD (Chính) (required) - format: "J00 - Viêm mũi họng"
    - Bệnh phụ (optional) - format: "B97.4 - Vi rút hợp bào"
    - Chẩn đoán ra viện (optional) → symptom
    - Phân loại (optional) → treatment_type (AI)
    - Feedback (optional) → tdv_feedback (TDV)
    - Lý do kê đơn (optional) → prescription_reason
    - Cách dùng (ignored)
    - SL (ignored)
    """
    logger.info(f"[ETL] Starting process_raw_log for batch: {batch_id}")
    
    try:
        # 1. Parse CSV from text content
        reader = csv.DictReader(io.StringIO(text_content))
        rows = list(reader)
        logger.info(f"[ETL] Parsed {len(rows)} rows from CSV")
        
        if not rows:
            logger.warning(f"[ETL] No rows found in batch {batch_id}")
            return
        
        # 2. Connect to DB
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 3. Ensure new columns exist (migration)
        _ensure_kb_columns(cursor)
        conn.commit()
        
        # 4. Process each row
        inserted = 0
        updated = 0
        errors = 0
        
        for row in rows:
            try:
                # === DRUG INFO ===
                drug_name = row.get('Tên thuốc', '').strip()
                if not drug_name:
                    errors += 1
                    continue
                drug_name_norm = normalize_text(drug_name)
                
                # === PRIMARY DISEASE ===
                primary_icd_raw = row.get('Mã ICD (Chính)', '').strip()
                if not primary_icd_raw:
                    errors += 1
                    continue
                disease_icd, disease_name = parse_icd_field(primary_icd_raw)
                disease_name_norm = normalize_text(disease_name) if disease_name else ''
                disease_ref_id = lookup_disease_ref_id(cursor, disease_icd)
                
                # === SECONDARY DISEASE ===
                secondary_raw = row.get('Bệnh phụ', '').strip()
                secondary_icd, secondary_name = parse_icd_field(secondary_raw)
                secondary_name_norm = normalize_text(secondary_name) if secondary_name else ''
                secondary_ref_id = lookup_disease_ref_id(cursor, secondary_icd)
                
                # === CLASSIFICATION ===
                treatment_type = row.get('Phân loại', '').strip()
                tdv_feedback = row.get('Feedback', '').strip()
                
                # === OTHER FIELDS ===
                symptom = row.get('Chẩn đoán ra viện', '').strip()
                prescription_reason = row.get('Lý do kê đơn', '').strip()
                
                # === CHECK IF EXISTS (by drug + primary disease) ===
                cursor.execute("""
                    SELECT id, frequency FROM knowledge_base 
                    WHERE drug_name_norm = ? AND disease_icd = ?
                """, (drug_name_norm, disease_icd))
                
                existing = cursor.fetchone()
                
                if existing:
                    # UPDATE: Increment frequency
                    existing_id = existing['id'] if isinstance(existing, dict) else existing[0]
                    existing_freq = existing['frequency'] if isinstance(existing, dict) else existing[1]
                    new_freq = (existing_freq or 0) + 1
                    
                    cursor.execute("""
                        UPDATE knowledge_base 
                        SET frequency = ?, 
                            treatment_type = COALESCE(?, treatment_type),
                            tdv_feedback = COALESCE(?, tdv_feedback),
                            symptom = COALESCE(?, symptom),
                            prescription_reason = COALESCE(?, prescription_reason),
                            last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_freq, treatment_type or None, tdv_feedback or None, 
                          symptom or None, prescription_reason or None, existing_id))
                    updated += 1
                else:
                    # INSERT: New record
                    cursor.execute("""
                        INSERT INTO knowledge_base 
                        (drug_name, drug_name_norm, drug_ref_id,
                         disease_icd, disease_name, disease_name_norm, disease_ref_id,
                         secondary_disease_icd, secondary_disease_name, secondary_disease_name_norm, secondary_disease_ref_id,
                         treatment_type, tdv_feedback, symptom, prescription_reason,
                         frequency, batch_id, last_updated)
                        VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                    """, (
                        drug_name, drug_name_norm,
                        disease_icd, disease_name, disease_name_norm, disease_ref_id,
                        secondary_icd, secondary_name, secondary_name_norm, secondary_ref_id,
                        treatment_type, tdv_feedback, symptom, prescription_reason,
                        batch_id
                    ))
                    inserted += 1
                    
            except Exception as row_err:
                logger.error(f"[ETL] Row error: {row_err}")
                errors += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"[ETL] Batch {batch_id} complete: {inserted} inserted, {updated} updated, {errors} errors")
        
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
