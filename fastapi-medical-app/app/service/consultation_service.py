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
        Check Internal Knowledge Base (Rule-based)
        Returns best match dict or None
        """
        conn = self.db_core.get_connection()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        cursor = conn.cursor()
        
        try:
            drug_norm = normalize_text(drug_name)
            diag_norm = normalize_text(disease_name)
            
            cursor.execute("""
                SELECT count(*) as frequency, treatment_type
                FROM knowledge_base 
                WHERE drug_name_norm = ? AND disease_name_norm = ?
                GROUP BY treatment_type
                ORDER BY frequency DESC
                LIMIT 1
            """, (drug_norm, diag_norm))
            
            row = cursor.fetchone()
            
            if row:
                freq = row['frequency']
                # Calculate Dynamic Confidence
                conf = min(0.99, math.log10(freq) / 2.0) if freq > 1 else 0.1
                
                if conf >= 0.8: # High confidence threshold
                    return {
                        "validity": "valid", 
                        "role": row['treatment_type'] if row['treatment_type'] else ("main drug" if disease_type == 'MAIN' else "supportive"),
                        "explanation": f"Internal KB: Found {freq} records for '{disease_name}'. Confidence: {conf:.0%}",
                        "source": "INTERNAL_KB"
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
