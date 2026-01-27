import math
from typing import List, Dict, Optional, Tuple
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
                    # Vote & Promote: Priority TDV > AI
                    # TDV null/empty/"valid" = TDV agrees with AI
                    tdv_role = self._get_valid_role(match.get('tdv_feedback'))
                    ai_role = self._get_valid_role(match.get('treatment_type'))
                    
                    if tdv_role:
                        role = tdv_role
                        source = "INTERNAL_KB_TDV"
                        explanation = f"Expert Verified: '{role}' by TĐV. (Match: {match['match_method']})"
                    elif ai_role:
                        # TDV null = agrees with AI
                        role = ai_role
                        source = "INTERNAL_KB_AI"
                        explanation = f"AI Classification: '{role}' (TĐV đồng ý). (Match: {match['match_method']})"
                    else:
                        # RULE: Nếu có match trong KB nhưng role trống/valid → mặc định main drug
                        # Vì thuốc đã tồn tại trong KB = đã được validate trước đó
                        role = "main drug"
                        source = "INTERNAL_KB_DEFAULT"
                        explanation = f"Thuốc có trong KB, mặc định là thuốc điều trị chính. (Match: {match['match_method']})"
                    
                    category, validity, clean_role = self.auto_correct_mapping(role)
                    
                    results.append({
                        "id": item.id,
                        "name": item.name,
                        "category": category,
                        "validity": validity,
                        "role": clean_role,
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
    def check_knowledge_base_strict(self, drug_name_norm: str, disease_icd: str) -> Optional[Dict]:
        """
        Strict Lookup by Normalized Drug Name + Disease ICD.
        """
        conn = self.db_core.get_connection()
        # conn.row_factory = sqlite3.Row # Removed: DatabaseCore handles this (Dict cursor)
        cursor = conn.cursor()
        
        try:
            # Query for exact match on drug_name_norm + disease_icd
            # ? placeholders are handled by DatabaseCore wrapper if Postgres
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
                    category, validity, clean_role = self.auto_correct_mapping(role)
                    
                    return {
                        "category": category,
                        "validity": validity,
                        "role": clean_role,
                        "explanation": f"Expert Verified: Classified as '{clean_role}' bởi TĐV.",
                        "source": "INTERNAL_KB_TDV"
                    }
            
            # 2. Check for AI Ingested Data
            for row in rows:
                raw_role = row['treatment_type']
                if raw_role:
                    role = self._clean_role_string(raw_role)
                    category, validity, clean_role = self.auto_correct_mapping(role)
                    
                    return {
                        "category": category,
                        "validity": validity,
                        "role": clean_role,
                        "explanation": "Internal KB (AI): Ingested from historical usage.",
                        "source": "INTERNAL_KB_AI"
                    }
                    
            return None
            
        finally:
            conn.close()

    def _clean_role_string(self, raw: str) -> str:
        """
        Use AI to infer the correct role from raw DB value.
        
        Delegates to ai_consult_service.infer_role_from_data() which:
        1. Calls Azure OpenAI to interpret the data
        2. Falls back to simple extraction if AI unavailable
        
        Examples:
        - '["drug", "valid", "main drug"]' → 'main drug'
        - '["drug", "invalid"]' → '' (no role)
        - '["valid", "secondary drug", "main drug"]' → AI decides
        """
        from app.service.ai_consult_service import infer_role_from_data
        return infer_role_from_data(raw)

    def _get_valid_role(self, raw_value: Optional[str]) -> Optional[str]:
        """
        Extract valid role from raw value.
        Returns None if value is empty or non-informative (null, valid, invalid, etc.)
        This supports Vote & Promote logic: TDV null/empty = agrees with AI.
        """
        if not raw_value:
            return None
        
        cleaned = self._clean_role_string(raw_value)
        
        # Reject non-role values
        # "valid" is not a role, just confirmation that drug is valid
        # "invalid" and "unknown" are also not informative roles
        invalid_values = ['', 'null', 'none', 'valid', 'invalid', 'unknown']
        if cleaned.lower().strip() in invalid_values:
            return None
        
        return cleaned

    def auto_correct_mapping(self, role: str) -> Tuple[str, str, str]:
        """
        Auto-correct category and validity based on role (Source of Truth).
        Returns: (category, validity, role)
        
        ROLE is the source of truth:
        - role determines category AND validity
        - Invalid combinations are IMPOSSIBLE because we derive from role
        
        Rules:
          - NODRUG roles: supplement, medical equipment, cosmeceuticals → category='nodrug', validity=''
          - DRUG roles: main drug, secondary drug → category='drug', validity='valid'
          - No role or invalid → category='drug', validity='invalid'
        """
        if not role:
            return "drug", "invalid", ""
        
        role_lower = role.lower().strip()
        
        # ========== NODRUG ROLES ==========
        nodrug_roles = [
            "supplement", "thực phẩm chức năng",
            "cosmeceuticals", "dược mỹ phẩm",
            "medical equipment", "thiết bị y tế",
            "medical supply", "vật tư y tế"
        ]
        
        if role_lower in nodrug_roles:
            return "nodrug", "", role
        
        # ========== DRUG ROLES (VALID) ==========
        drug_valid_roles = ["main drug", "secondary drug"]
        
        if role_lower in drug_valid_roles:
            return "drug", "valid", role
        
        # ========== INVALID DRUG ==========
        if "invalid" in role_lower or "contraindication" in role_lower:
            return "drug", "invalid", role
        
        # ========== UNKNOWN ROLE ==========
        # Log warning for unknown roles
        print(f"[WARNING] Unknown role '{role}' - defaulting to drug/valid")
        return "drug", "valid", role
    
    def validate_output(self, category: str, validity: str, role: str) -> Tuple[str, str, str]:
        """
        Final validation to ensure output consistency.
        Fixes any invalid combinations that might slip through.
        
        FORBIDDEN COMBINATIONS (will be auto-corrected):
        - category='nodrug' + role='main drug' → IMPOSSIBLE
        - category='drug' + role='supplement' → IMPOSSIBLE
        """
        role_lower = role.lower().strip() if role else ""
        
        # Define role groups
        nodrug_roles = {"supplement", "thực phẩm chức năng", "cosmeceuticals", 
                        "dược mỹ phẩm", "medical equipment", "thiết bị y tế", 
                        "medical supply", "vật tư y tế"}
        drug_roles = {"main drug", "secondary drug"}
        
        # Validate: If role is a drug role, category MUST be 'drug'
        if role_lower in drug_roles and category != "drug":
            print(f"[FIX] Invalid combo: category='{category}' + role='{role}' → Correcting to drug/valid")
            return "drug", "valid", role
        
        # Validate: If role is a nodrug role, category MUST be 'nodrug'
        if role_lower in nodrug_roles and category != "nodrug":
            print(f"[FIX] Invalid combo: category='{category}' + role='{role}' → Correcting to nodrug")
            return "nodrug", "", role
        
        return category, validity, role

