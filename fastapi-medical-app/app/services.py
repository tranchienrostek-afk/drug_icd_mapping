import os
import asyncio
from datetime import datetime
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from openai import AzureOpenAI
from app.core.utils import normalize_text, normalize_for_matching
from dotenv import load_dotenv

# NEW MODULES IMPORTS
from app.database.core import DatabaseCore
from app.service.drug_repo import DrugRepository
from app.service.drug_search_service import DrugSearchService
from app.service.drug_approval_service import DrugApprovalService
from app.service.ai_consult_service import analyze_treatment_group
from app.service.disease_service import DiseaseService
from app.service.monitor_service import MonitorService

load_dotenv()

# --- UTILS ---
DB_PATH = os.getenv("DB_PATH", "app/database/medical.db")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# --- CẤU HÌNH OPENAI (Lazy Init to avoid import-time errors) ---
_openai_client = None
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            _openai_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
            _openai_client = None
    return _openai_client

# --- DATABASE ENGINE CHO THUỐC ---
class DrugDbEngine:
    """
    [DEPRECATED/FACADE]
    This class is now a wrapper around the new modular services:
    - DatabaseCore
    - DrugApprovalService
    - MonitorService
    
    It is kept for backward compatibility with existing API calls.
    Please refer to `app/service/` for the actual implementation.
    """
    def __init__(self, db_path=DB_PATH):
        # 1. Initialize Core
        self.db_core = DatabaseCore(db_path)
        
        # 2. Initialize Sub-Services
        self.repo = DrugRepository(self.db_core)
        self.search_service = DrugSearchService(self.db_core)
        self.approval_service = DrugApprovalService(self.db_core)
        self.monitor_service = MonitorService(self.db_core)
        
        self.db_path = db_path
        # No longer maintaining state here directly

    # --- DELEGATED METHODS ---

    def get_connection(self):
        return self.db_core.get_connection()

    def _ensure_tables(self):
        # Already handled by DatabaseCore __init__
        pass

    def search(self, query):
        return self.search_service.search(query)

    async def search_drug_smart(self, query_name: str):
        return await self.search_service.search_drug_smart(query_name)

    async def get_drug_by_id(self, row_id):
        return await self.repo.get_drug_by_id(row_id)

    def get_all_drugs(self, page=1, limit=10, search=None):
        return self.repo.get_all_drugs(page, limit, search)

    def save_verified_drug(self, drug_data):
        return self.approval_service.save_verified_drug(drug_data)

    def get_pending_stagings(self):
        return self.approval_service.get_pending_stagings()

    def approve_staging(self, staging_id, user):
        return self.approval_service.approve_staging(staging_id, user)

    def reject_staging(self, staging_id, user="system"):
        return self.approval_service.reject_staging(staging_id, user)

    def clear_all_staging(self, user="system"):
        return self.approval_service.clear_all_staging(user)

    def update_staging(self, staging_id, data, user="system"):
        return self.approval_service.update_staging(staging_id, data, user)

    # --- LEGACY METHODS (May strictly belong to internal helpers) ---
    
    def _update_fts(self, cursor, row_id, ten, hoat_chat, cong_ty, search_text):
        # This was an internal helper. If external code called it, it might break.
        # But 'DrugDbEngine' consumers likely only used public methods.
        # It is re-implemented in ApprovalService.
        pass

    def _load_vector_cache(self):
        return self.search_service._load_vector_cache()

    # --- MORE LEGACY METHODS (Needed by admin.py) ---
    def get_drugs_list(self, page=1, limit=20, search=""):
        return self.repo.get_all_drugs(page, limit, search)
    
    def delete_drug(self, sdk):
        return self.repo.delete_drug(sdk)
    
    def delete_drug_by_id(self, row_id):
        return self.repo.delete_drug_by_id(row_id)
    
    def get_links_list(self, page=1, limit=20, search=""):
        return self.repo.get_links_list(page, limit, search)
    
    def delete_link(self, sdk, icd_code):
        return self.repo.delete_link(sdk, icd_code)
    
    async def log_raw_data(self, batch_id: str, content: str, source: str = "api"):
        """
        Log raw data to the database for audit/replay purposes.
        """
        try:
            conn = self.db_core.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO raw_logs (batch_id, raw_content, source_ip, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (batch_id, content, source))
            conn.commit()
            conn.close()
            print(f"[LogRawData] Saved batch {batch_id} to DB")
            return True
        except Exception as e:
            print(f"[LogRawData] Error saving batch {batch_id}: {e}")
            return False
    
    def check_knowledge_base(self, sdks, icds):
        # Delegate to DiseaseService
        disease_service = DiseaseService(self.db_core)
        return disease_service.check_knowledge_base(sdks, icds)
    
    def link_drug_disease(self, data: dict) -> dict:
        """
        Create a link between a drug and a disease in drug_disease_links table.
        
        Args:
            data: dict with keys:
                - drug_name: str (required)
                - disease_name: str (required)
                - sdk: str (optional)
                - icd_code: str (optional)
                - treatment_note: str (optional)
                - is_verified: int (optional, default 0)
                - coverage_type: str (optional)
                - created_by: str (optional, default 'system')
                - status: str (optional, default 'active')
        
        Returns:
            dict with status and message
        """
        try:
            conn = self.db_core.get_connection()
            cursor = conn.cursor()
            
            # Extract data with defaults
            drug_name = data.get('drug_name', '')
            disease_name = data.get('disease_name', '')
            sdk = data.get('sdk', '')
            # Normalize ICD to match ConsultationService logic (lowercase)
            icd_code = data.get('icd_code', '').strip().lower()
            treatment_note = data.get('treatment_note', '')
            is_verified = data.get('is_verified', 0)
            coverage_type = data.get('coverage_type', '')
            created_by = data.get('created_by', 'system')
            status = data.get('status', 'active')
            
            if not drug_name or not disease_name:
                return {"status": "error", "message": "drug_name and disease_name are required"}
            
            # Check if link already exists
            cursor.execute("""
                SELECT id FROM drug_disease_links 
                WHERE sdk = ? AND icd_code = ?
            """, (sdk, icd_code))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing link
                cursor.execute("""
                    UPDATE drug_disease_links 
                    SET treatment_note = ?, is_verified = ?, coverage_type = ?, status = ?
                    WHERE id = ?
                """, (treatment_note, is_verified, coverage_type, status, existing['id']))
                conn.commit()
                conn.close()
                return {"status": "updated", "message": f"Link updated: {sdk} <-> {icd_code}", "id": existing['id']}
            else:
                # Insert new link
                cursor.execute("""
                    INSERT INTO drug_disease_links 
                    (sdk, icd_code, treatment_note, is_verified, coverage_type, created_by, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (sdk, icd_code, treatment_note, is_verified, coverage_type, created_by, status))
                
                new_id = cursor.lastrowid
                
                # --- SYNC TO KNOWLEDGE_BASE ---
                # Check if entry exists in KB to avoid duplicates or update it
                drug_norm = normalize_text(drug_name)
                # disease_norm = normalize_text(disease_name) # Schema has disease_name_norm but lookup uses icd
                
                cursor.execute("""
                    SELECT id FROM knowledge_base 
                    WHERE drug_name_norm = ? AND disease_icd = ?
                """, (drug_norm, icd_code))
                kb_row = cursor.fetchone()
                
                if kb_row:
                    cursor.execute("""
                        UPDATE knowledge_base
                        SET treatment_type = ?, tdv_feedback = ?, frequency = frequency + 1, last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (coverage_type, treatment_note, kb_row['id']))
                else:
                    cursor.execute("""
                        INSERT INTO knowledge_base
                        (drug_name, drug_name_norm, disease_icd, disease_name, treatment_type, tdv_feedback, frequency, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    """, (drug_name, drug_norm, icd_code, disease_name, coverage_type, treatment_note))
                
                conn.commit()
                conn.close()
                return {"status": "created", "message": f"Link and KB Sync created: {sdk} <-> {icd_code}", "id": new_id}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}


# --- DISEASE DB ENGINE (Wrapper around DiseaseService) ---
class DiseaseDbEngine:
    """
    Wrapper class for disease database operations.
    Delegates to DiseaseService for actual implementation.
    """
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._service = None
    
    @property
    def service(self):
        if self._service is None:
            db_core = DatabaseCore(self.db_path)
            self._service = DiseaseService(db_core)
        return self._service
        
    def search(self, name, icd10=None):
        return self.service.search(name, icd10)
    
    def get_diseases_list(self, page=1, limit=20, search=""):
        return self.service.get_diseases_list(page, limit, search)
    
    def save_disease(self, data):
        return self.service.save_disease(data)
    
    def delete_disease(self, icd_code):
        return self.service.delete_disease(icd_code)
    
    def delete_disease_by_id(self, row_id):
        return self.service.delete_disease_by_id(row_id)


# --- SCRAPE ICD WEB ---
async def scrape_icd_web(icd_code: str):
    """
    Scrape ICD information from web.
    Uses the crawler module if needed.
    """
    # For now, return None to indicate no web result
    # Could be implemented using app.service.crawler for ICD sites
    return None