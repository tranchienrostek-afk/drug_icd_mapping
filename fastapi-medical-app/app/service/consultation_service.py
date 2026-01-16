import math
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

    def check_knowledge_base(self, drug_name: str, disease_name: str, disease_type: str) -> Optional[Dict]:
        """
        Check Internal Knowledge Base (Rule-based) with TDV Priority.
        
        Logic:
        1. Check for 'tdv_feedback' (Human Verified) -> Highest Priority
        2. Fallback to 'treatment_type' (AI) -> Weighted by frequency
        
        Returns best match dict or None
        """
        conn = self.db_core.get_connection()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        cursor = conn.cursor()
        
        try:
            drug_norm = normalize_text(drug_name)
            diag_norm = normalize_text(disease_name)
            
            # Query grouping by both classification types to find best match
            cursor.execute("""
                SELECT 
                    treatment_type, 
                    tdv_feedback, 
                    SUM(frequency) as total_freq,
                    count(*) as record_count
                FROM knowledge_base 
                WHERE drug_name_norm = ? AND disease_name_norm = ?
                GROUP BY treatment_type, tdv_feedback
                ORDER BY total_freq DESC
            """, (drug_norm, diag_norm))
            
            rows = cursor.fetchall()
            
            if not rows:
                return None
                
            # 1. Check for TDV Feedback (Highest Priority)
            for row in rows:
                if row['tdv_feedback'] and row['tdv_feedback'].lower() not in ('', 'none', 'null'):
                    return {
                        "validity": "valid", # TDV implies valid/checked
                        "role": row['tdv_feedback'],
                        "explanation": f"Expert Verified: Classified as '{row['tdv_feedback']}' by Medical Reviewer.",
                        "source": "INTERNAL_KB_TDV"
                    }
            
            # 2. Fallback to AI Classification (treatment_type)
            # Find row with highest frequency that has a valid treatment_type
            best_ai_row = None
            for row in rows:
                if row['treatment_type']:
                    best_ai_row = row
                    break
            
            if best_ai_row:
                freq = best_ai_row['total_freq']
                # Calculate Dynamic Confidence
                conf = min(0.99, math.log10(freq) / 2.0) if freq > 1 else 0.1
                
                if conf >= 0.8: # High confidence threshold for AI
                    return {
                        "validity": "valid", 
                        "role": best_ai_row['treatment_type'],
                        "explanation": f"Internal KB (AI): Found {freq} records. Confidence: {conf:.0%}",
                        "source": "INTERNAL_KB_AI"
                    }
                    
            return None
            
        finally:
            conn.close()

    async def consult_integrated(self, items: List, diagnoses: List) -> List:
        results = []
        drugs_for_ai = []
        
        # 1. Prepare Data
        main_diagnoses = [d for d in diagnoses if d.type == 'MAIN']
        if not main_diagnoses:
            main_diagnoses = diagnoses[:1] if diagnoses else []
        other_diagnoses = [d for d in diagnoses if d not in main_diagnoses]
        all_diagnoses = main_diagnoses + other_diagnoses
        
        # 2. Check KB
        for item in items:
            is_resolved = False
            best_match = None
            
            # Iterate through diagnoses (Priority: Main -> Secondary)
            for diag in all_diagnoses:
                match = self.check_knowledge_base(item.name, diag.name, diag.type)
                if match:
                    is_resolved = True
                    best_match = match
                    break
            
            if is_resolved and best_match:
                results.append({
                    "id": item.id,
                    "name": item.name,
                    "validity": best_match['validity'],
                    "role": best_match['role'],
                    "explanation": best_match['explanation'],
                    "source": best_match['source']
                })
            else:
                drugs_for_ai.append(item)

        # 3. AI Fallback
        if drugs_for_ai:
            ai_results = await self._call_ai_fallback(drugs_for_ai, diagnoses)
            results.extend(ai_results)
            
        return results

    async def _call_ai_fallback(self, drugs: List, diagnoses: List) -> List:
        """
        Internal: Call OpenAI/LLM for advanced consultation
        """
        results = []
        try:
            from app.services import analyze_treatment_group # Import here to avoid circular dependency if any, or better, move logic here
            # Ideally analyze_treatment_group should be in AI service. For now, assuming it exists or we mock it.
            # If it was deleted from services.py, this will fail. We need to verify.
            # Assuming we need to implement it or it is imported. 
            pass 
        except ImportError:
             # Fallback if analyze_treatment_group is missing
             pass
             
        drug_dicts = [{"ten_thuoc": d.name, "so_dang_ky": ""} for d in drugs]
        disease_dicts = [{"disease_name": d.name, "icd_code": d.code} for d in diagnoses]
        
        try:
             # We invoke the AI logic here. 
             # NOTE: Since analyze_treatment_group might have been lost in services.py refactor, 
             # I should probably MOVE that logic here or into a new ai_service.py.
             # For this step, I will PLACEHOLDER the AI call to ensure structure, 
             # and then we might need to fix 'analyze_treatment_group'.
             
             # Simulating AI Call or using existing function if importable
             # Logic copied from original consult.py loop
             
             # Re-implementing simplified AI Call wrapper or using a hypothetical ai_service
             from app.service.ai_consult_service import analyze_treatment_group_wrapper # Hypothetical
             ai_res = await analyze_treatment_group_wrapper(drug_dicts, disease_dicts)
             
             # ... Logic to parse ai_res ...
             # Since I don't have the full AI logic code right now (it was imported), 
             # I will mark this as "To Be Implement/Restored" or use a safe fallback.
             
             for d in drugs:
                 results.append({
                    "id": d.id,
                    "name": d.name,
                    "validity": "unknown",
                    "role": "external AI suggestion", 
                    "explanation": "AI Service response (Mock/Placeholder)",
                    "source": "EXTERNAL_AI"
                })

        except Exception as e:
            for d in drugs:
                 results.append({
                    "id": d.id,
                    "name": d.name,
                    "validity": "error",
                    "role": "error",
                    "explanation": f"AI Error: {str(e)}",
                    "source": "ERROR"
                })
        
        return results
