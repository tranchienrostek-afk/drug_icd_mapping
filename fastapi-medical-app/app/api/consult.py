
from fastapi import APIRouter, HTTPException
from typing import List
from app.services import DrugDbEngine
from app.service.consultation_service import ConsultationService
from app.models import ConsultRequest, ConsultResponse, ConsultResult

router = APIRouter()
db = DrugDbEngine()
# Instantiate Service (using DB Core from Engine or creating new one)
consultation_service = ConsultationService(db_core=db.db_core)

@router.post("/consult_integrated", response_model=ConsultResponse)
async def consult_integrated(payload: ConsultRequest):
    """
    Hybrid Consultation API:
    1. Check Internal Knowledge Base (Rule-based).
    2. Fallback to External AI (if needed).
    """
    try:
        results_data = await consultation_service.process_integrated_consultation(payload)
        
        # Map Dict results to Pydantic Models
        results = [ConsultResult(**item) for item in results_data]
        
        return ConsultResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
