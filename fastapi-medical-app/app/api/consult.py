
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services import DrugDbEngine, analyze_treatment_group
from app.utils import normalize_text

router = APIRouter()
db = DrugDbEngine()

# --- Request Models ---
class DrugItem(BaseModel):
    id: str
    name: str

class DiagnosisItem(BaseModel):
    code: str
    name: str
    type: str # MAIN / SECONDARY

class ConsultRequest(BaseModel):
    request_id: str
    items: List[DrugItem]
    diagnoses: List[DiagnosisItem]
    symptom: Optional[str] = None

# --- Response Models ---
class ConsultResult(BaseModel):
    id: str
    name: str
    category: str = "drug"
    validity: str
    role: str
    explanation: str
    source: str

class ConsultResponse(BaseModel):
    results: List[ConsultResult]

@router.post("/consult_integrated", response_model=ConsultResponse)
async def consult_integrated(payload: ConsultRequest):
    """
    Hybrid Consultation API:
    1. Check Internal Knowledge Base (Rule-based).
    2. Fallback to External AI (if needed).
    """
    results = []
    
    # 1. Prepare Data
    drug_map = {item.id: item for item in payload.items}
    
    # Check against Main Diagnosis first.
    main_diagnoses = [d for d in payload.diagnoses if d.type == 'MAIN']
    if not main_diagnoses:
        # Fallback to first if no MAIN marked
        main_diagnoses = payload.diagnoses[:1] if payload.diagnoses else []
    
    other_diagnoses = [d for d in payload.diagnoses if d not in main_diagnoses]
    all_diagnoses = main_diagnoses + other_diagnoses
        
    # Collect logic
    drugs_for_ai = []
    
    conn = db.get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        
        for item in payload.items:
            # 2. Check KB
            is_resolved = False
            best_match = None
            
            drug_norm = normalize_text(item.name)
            
            # Iterate through diagnoses (Priority: Main -> Secondary)
            for diag in all_diagnoses:
                diag_norm = normalize_text(diag.name)
                
                # Check DB
                cursor.execute("""
                    SELECT frequency, confidence_score 
                    FROM knowledge_base 
                    WHERE drug_name_norm = ? AND disease_name_norm = ?
                """, (drug_norm, diag_norm))
                row = cursor.fetchone()
                
                if row:
                    conf = row['confidence_score']
                    # THRESHOLD
                    if conf >= 0.8: # High confidence
                        is_resolved = True
                        best_match = {
                            "validity": "valid", 
                            "role": "main drug" if diag.type == 'MAIN' else "supportive",
                            "explanation": f"Internal KB: Used {row['frequency']} times for '{diag.name}'. Confidence: {conf:.0%}",
                            "source": "INTERNAL_KB"
                        }
                        break
            
            if is_resolved and best_match:
                results.append(ConsultResult(
                    id=item.id,
                    name=item.name,
                    validity=best_match['validity'],
                    role=best_match['role'],
                    explanation=best_match['explanation'],
                    source=best_match['source']
                ))
            else:
                # Add to AI queue
                drugs_for_ai.append(item)
                
        # 3. AI Fallback
        if drugs_for_ai:
            
            drug_dicts = [{"ten_thuoc": d.name, "so_dang_ky": ""} for d in drugs_for_ai]
            disease_dicts = [{"disease_name": d.name, "icd_code": d.code} for d in payload.diagnoses]
            
            # Call AI
            try:
                ai_res = analyze_treatment_group(drug_dicts, disease_dicts)
                
                # Create lookup for input names
                ai_drug_lookup = {d.name.lower(): d.id for d in drugs_for_ai}
                
                processed_ai_ids = set()
                
                if ai_res and 'results' in ai_res:
                    for group in ai_res['results']:
                        for med_pair in group.get('medications', []):
                            # med_pair is [name_sdk, reason]
                            if len(med_pair) >= 2:
                                raw_name_sdk = med_pair[0]
                                reason = med_pair[1]
                                
                                # Extract name (remove sdk if present)
                                # Simple split ' ('
                                name_only = raw_name_sdk.split(' (')[0].strip()
                                
                                # Try match
                                item_id = ai_drug_lookup.get(name_only.lower())
                                
                                if item_id:
                                    results.append(ConsultResult(
                                        id=item_id,
                                        name=name_only,
                                        validity="valid",
                                        role="external AI suggestion",
                                        explanation=f"AI Suggestion: {reason}",
                                        source="EXTERNAL_AI"
                                    ))
                                    processed_ai_ids.add(item_id)
                
                # Handle leftovers (AI didn't mention them)
                for d in drugs_for_ai:
                    if d.id not in processed_ai_ids:
                         results.append(ConsultResult(
                            id=d.id,
                            name=d.name,
                            validity="unknown",
                            role="unknown",
                            explanation="AI provided no specific mapping.",
                            source="EXTERNAL_AI_FALLBACK"
                        ))
            except Exception as e:
                # AI Error
                for d in drugs_for_ai:
                     results.append(ConsultResult(
                        id=d.id,
                        name=d.name,
                        validity="error",
                        role="error",
                        explanation=f"AI System Error: {str(e)}",
                        source="ERROR"
                    ))

    finally:
        conn.close()
        
    return ConsultResponse(results=results)
