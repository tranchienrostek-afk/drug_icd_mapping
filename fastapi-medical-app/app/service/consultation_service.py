import math
import sqlite3
from typing import List, Dict, Optional
from app.models import ConsultResult 
from app.database.core import DatabaseCore
from app.core.utils import normalize_text
from app.service.kb_fuzzy_match_service import KBFuzzyMatchService

class ConsultationService:
    def __init__(self, db_core: DatabaseCore = None):
        if db_core is None:
            self.db_core = DatabaseCore()
        else:
            self.db_core = db_core
        
        # Initialize fuzzy matcher for KB lookups
        self.kb_matcher = KBFuzzyMatchService(self.db_core)

    async def process_integrated_consultation(self, request) -> List[Dict]:
        """
        Integrated Consultation: Internal KB with Fuzzy Matching.
        
        Logic:
        1. Iterate Drug x Diagnosis pairs.
        2. Use KBFuzzyMatchService for fuzzy drug name lookup.
        3. Return TDV > AI classification priority.
        """
        results = []
        
        for item in request.items:
            is_resolved = False
            
            for diag in request.diagnoses:
                disease_icd = diag.code.strip().lower()
                
                # Use fuzzy matching instead of exact
                match = self.kb_matcher.find_best_match_with_icd(item.name, disease_icd)
                
                if match:
                    # Determine source based on tdv_feedback or treatment_type
                    if match.get('tdv_feedback') and match['tdv_feedback'].lower() not in ('', 'none', 'null'):
                        role = self._clean_role_string(match['tdv_feedback'])
                        source = "INTERNAL_KB_TDV"
                        explanation = f"Expert Verified: Classified as '{role}' bởi TĐV. (Match: {match['match_method']})"
                    elif match.get('treatment_type'):
                        role = self._clean_role_string(match['treatment_type'])
                        source = "INTERNAL_KB_AI"
                        explanation = f"Internal KB (AI): Ingested from historical usage. (Match: {match['match_method']})"
                    else:
                        continue
                    
                    results.append({
                        "id": item.id,
                        "name": item.name,
                        "category": "drug",
                        "validity": "valid",
                        "role": role,
                        "explanation": explanation,
                        "source": source,
                        "match_score": match.get('match_score'),
                        "matched_name": match.get('drug_name_norm')
                    })
                    is_resolved = True
                    break  # Found match, stop checking other diagnoses
            
            if not is_resolved:
                results.append({
                    "id": item.id,
                    "name": item.name,
                    "category": "drug",
                    "validity": "unknown",
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
