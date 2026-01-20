import math
import sqlite3
from typing import List, Dict, Optional
from app.models import ConsultResult 
from app.database.core import DatabaseCore
from app.core.utils import normalize_text
# from app.services import analyze_treatment_group # We are moving this logic here or to a separate AI module

class ConsultationService:
    def __init__(self, db_core: DatabaseCore = None):
        if db_core is None:
            self.db_core = DatabaseCore()
        else:
            self.db_core = db_core

    async def process_integrated_consultation(self, request) -> List[Dict]:
        """
        Integrated Consultation: Internal KB Only.
        
        Logic:
        1. Iterate Drug x Diagnosis pairs.
        2. Normalize inputs.
        3. Query KB (Priority: TDV > AI).
        4. Skip if not found.
        """
        results = []
        
        # Pre-process diagnoses (Main + Secondary)
        # Actually, we treat them equally for interaction checking, 
        # but logically we might want to know which is MAIN.
        # The query does strict check on disease_icd.
        
        # 1. Iterate Inputs
        for item in request.items:
            # Normalize Drug Name
            dataset_drug_name = normalize_text(item.name)
            is_resolved = False
            
            for diag in request.diagnoses:
                # Normalize Disease (ICD Code should be lowercase to match DB)
                disease_icd = diag.code.strip().lower()
                
                # 2. Check KB
                match = self.check_knowledge_base_strict(dataset_drug_name, disease_icd)
                
                if match:
                    results.append({
                        "id": item.id,
                        "name": item.name,
                        "category": "drug",
                        "validity": match['validity'],
                        "role": match['role'],
                        "explanation": match['explanation'],
                        "source": match['source']
                    })
                    is_resolved = True
            
            # 3. Handle Not Found (Keep in list per user request)
            if not is_resolved:
                 results.append({
                    "id": item.id,
                    "name": item.name,
                    "category": "drug",
                    "validity": "unknown", # Or empty string? User said "trống" but Model requires str
                    "role": "", 
                    "explanation": "Không tìm thấy thông tin trong cơ sở dữ liệu.",
                    "source": "INTERNAL_KB_EMPTY"
                })
        
        return results

    def check_knowledge_base_strict(self, drug_name_norm: str, disease_icd: str) -> Optional[Dict]:
        """
        Strict Lookup by Normalized Drug Name + Disease ICD.
        """
        conn = self.db_core.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Query for exact match on drug_name_norm + disease_icd
            cursor.execute("""
                SELECT 
                    treatment_type, 
                    tdv_feedback, 
                    frequency
                FROM knowledge_base 
                WHERE drug_name_norm = ? AND disease_icd = ?
                ORDER BY last_updated DESC
            """, (drug_name_norm, disease_icd))
            
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Logic: Iterate to find best match (Priority: TDV > AI)
            
            # 1. Check for TDV Feedback
            for row in rows:
                raw_role = row['tdv_feedback']
                if raw_role and raw_role.lower() not in ('', 'none', 'null'):
                    # Clean the role string (remove JSON artifacts if present)
                    role = self._clean_role_string(raw_role)
                    
                    return {
                        "validity": "valid",
                        "role": role,
                        "explanation": f"Expert Verified: Classified as '{role}' bởi TĐV.",
                        "source": "INTERNAL_KB_TDV"
                    }
            
            # 2. Check for AI Ingested Data
            for row in rows:
                raw_role = row['treatment_type']
                if raw_role:
                    role = self._clean_role_string(raw_role)
                    return {
                        "validity": "valid",
                        "role": role,
                        "explanation": "Internal KB (AI): Ingested from historical usage.",
                        "source": "INTERNAL_KB_AI"
                    }
                    
            return None
            
        finally:
            conn.close()

    def _clean_role_string(self, raw: str) -> str:
        """
        Helper to clean JSON-like or dirty strings from DB.
        Ex: '["{valid}"]' -> 'valid'
            '["{secondary drug}"]' -> 'secondary drug'
        """
        if not raw: return ""
        s = raw.strip()
        
        # Remove JSON list brackets
        s = s.replace('[', '').replace(']', '')
        
        # Remove quotes and curly braces
        s = s.replace('"', '').replace("'", '').replace('{', '').replace('}', '')
        
        return s.strip()
