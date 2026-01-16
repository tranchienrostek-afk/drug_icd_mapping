import pandas as pd
import re
import logging
from app.core.utils import normalize_drug_name, normalize_text

logger = logging.getLogger(__name__)

class EtlService:
    def __init__(self):
        pass

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load CSV data safely, handling potential encoding or delimiter issues.
        """
        try:
            df = pd.read_csv(file_path, on_bad_lines='skip')
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            raise

    def clean_and_deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean whitespace and deduplicate based on 'so_dang_ky'.
        Priority given to records with more non-null values.
        """
        if df.empty:
            return df
            
        initial_count = len(df)
        
        # 1. Standardize Column Names (strip)
        df.columns = df.columns.str.strip()
        
        # 2. Strip whitespace in string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' string with actual None/NaN if needed, but pandas handles NaN
            
        # 3. Handle 'so_dang_ky'
        if 'so_dang_ky' in df.columns:
            # Score each row based on completeness (number of non-null, non-empty fields)
            df['completeness_score'] = df.apply(lambda row: sum(1 for x in row if x and str(x).lower() != 'nan' and str(x).strip() != ''), axis=1)
            
            # Sort by completeness (descending) so the best record is first
            df = df.sort_values(by=['so_dang_ky', 'completeness_score'], ascending=[True, False])
            
            # Drop duplicates, keeping the first (most complete)
            df = df.drop_duplicates(subset=['so_dang_ky'], keep='first')
            
            # Drop helper column
            df = df.drop(columns=['completeness_score'])
            
        final_count = len(df)
        logger.info(f"Deduplication: Removed {initial_count - final_count} duplicate rows.")
        
        return df

    def extract_info_from_description(self, text: str) -> dict:
        """
        Heuristic to extract 'chi_dinh' and 'chong_chi_dinh' from 'noi_dung_dieu_tri'.
        """
        if not isinstance(text, str) or not text or text.lower() == 'nan':
            return {"chi_dinh": None, "chong_chi_dinh": None}
            
        # Simple extraction based on keywords
        chi_dinh = text
        chong_chi_dinh = None
        
        # Regex or split logic could be added here if the text structure is consistent.
        # For now, we assume 'noi_dung_dieu_tri' maps primarily to 'chi_dinh'.
        
        return {
            "chi_dinh": chi_dinh,
            "chong_chi_dinh": chong_chi_dinh
        }

    def process_for_import(self, df: pd.DataFrame) -> list:
        """
        Convert DataFrame to list of dicts ready for DB import.
        Map CSV columns to DB columns.
        """
        records = []
        for _, row in df.iterrows():
            # Basic mapping
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
            
            # Extract description details
            extracted = self.extract_info_from_description(row.get('noi_dung_dieu_tri'))
            record['chi_dinh'] = extracted['chi_dinh']
            record['chong_chi_dinh'] = extracted['chong_chi_dinh']
            
            # Clean up None/'nan' values
            cleaned_record = {k: v for k, v in record.items() if v and str(v).lower() != 'nan'}
            records.append(cleaned_record)
            
        return records


def process_raw_log(batch_id: str, text_content: str):
    """
    Process raw CSV log ingestion for Knowledge Base building.
    Expected CSV columns: drug_name, disease_name, icd_code (optional), phan_loai (optional)
    """
    import io
    import csv
    import sqlite3
    import os
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    logger.info(f"[ETL] Starting process_raw_log for batch: {batch_id}")
    
    DB_PATH = os.getenv("DB_PATH", "app/database/medical.db")
    
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
        cursor = conn.cursor()
        
        # 3. Process each row
        inserted = 0
        updated = 0
        errors = 0
        
        for row in rows:
            try:
                drug_name = row.get('drug_name', '').strip()
                disease_name = row.get('disease_name', '').strip()
                icd_code = row.get('icd_code', '').strip()
                phan_loai = row.get('phan_loai', 'unknown').strip()
                
                if not drug_name or not disease_name:
                    errors += 1
                    continue
                
                # Check if entry exists
                cursor.execute("""
                    SELECT id, frequency FROM knowledge_base 
                    WHERE drug_name = ? AND disease_name = ?
                """, (drug_name, disease_name))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update frequency
                    new_freq = existing[1] + 1
                    cursor.execute("""
                        UPDATE knowledge_base 
                        SET frequency = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_freq, existing[0]))
                    updated += 1
                else:
                    # Insert new
                    cursor.execute("""
                        INSERT INTO knowledge_base 
                        (drug_name, disease_name, icd_code, phan_loai, frequency, batch_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (drug_name, disease_name, icd_code, phan_loai, batch_id))
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

