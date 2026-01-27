from fastapi import APIRouter, HTTPException, Query
from app.services import DrugDbEngine, DiseaseDbEngine
from app.models import DrugConfirmRequest, DiseaseConfirmRequest

router = APIRouter()
drug_db = DrugDbEngine()
disease_db = DiseaseDbEngine()

# --- DRUGS ---
@router.get("/drugs")
def get_drugs(page: int = 1, limit: int = 20, search: str = ""):
    return drug_db.get_drugs_list(page, limit, search)

@router.post("/drugs")
def save_drug(payload: DrugConfirmRequest):
    result = drug_db.save_verified_drug(payload.model_dump())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.delete("/drugs/{sdk}")
def delete_drug(sdk: str):
    if drug_db.delete_drug(sdk):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Delete failed or Drug not found")

@router.delete("/drugs/id/{row_id}")
def delete_drug_by_id(row_id: int):
    if drug_db.delete_drug_by_id(row_id):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Delete failed or Drug ID not found")

# --- DISEASES ---
@router.get("/diseases")
def get_diseases(page: int = 1, limit: int = 20, search: str = ""):
    return disease_db.get_diseases_list(page, limit, search)

@router.post("/diseases")
def save_disease(payload: DiseaseConfirmRequest):
    result = disease_db.save_disease(payload.model_dump())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.delete("/diseases/{icd_code}")
def delete_disease(icd_code: str):
    if disease_db.delete_disease(icd_code):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Delete failed or Disease not found")
    
@router.delete("/diseases/id/{row_id}")
def delete_disease_by_id(row_id: int):
    if disease_db.delete_disease_by_id(row_id):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Delete failed or Disease ID not found")

# --- KNOWLEDGE LINKS ---
@router.get("/links")
def get_links(page: int = 1, limit: int = 20, search: str = ""):
    return drug_db.get_links_list(page, limit, search)

@router.delete("/links")
def delete_link(sdk: str, icd_code: str):
    if drug_db.delete_link(sdk, icd_code):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Delete failed or Link not found")

# --- MONITORING ---
@router.get("/monitor/stats")
def get_monitor_stats(days: int = 1):
    """
    Get System Stats:
    - Ingestion Batches (from knowledge_base)
    - API usage (from api_logs)
    """
    try:
        # DB Engine instance from global scope or dependency
        # We can reuse drug_db.monitor_service if exposed, or create new.
        # Ideally, we should add monitor_service to DrugDbEngine or similar wrapper.
        # But we added it to `DrugDbEngine` in `services.py` already!
        
        # In `services.py`, DrugDbEngine now has self.monitor_service
        monitor = drug_db.monitor_service
        
        ingestion_stats = monitor.get_ingestion_stats(limit=50)
        api_stats = monitor.get_api_stats(days=days)
        
        return {
            "status": "success",
            "ingestion": ingestion_stats,
            "api": api_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- REQUEST LOGS (NEW) ---
@router.get("/request_logs")
def get_request_logs(
    limit: int = 50, 
    endpoint: str = None,
    date_filter: str = None  # "today", "week", "month"
):
    """
    Get detailed request logs from monitor.db with filters.
    Returns summary stats, success/failure rates, and request list.
    """
    try:
        from app.monitor.service import get_monitor_stats, get_recent_logs, get_api_detailed_stats
        
        # Get detailed stats for each API
        mapping_stats = get_api_detailed_stats(endpoint="mapping", date_filter=date_filter)
        consult_stats = get_api_detailed_stats(endpoint="consult", date_filter=date_filter)
        
        # Get filtered logs
        logs = get_recent_logs(limit=limit, endpoint_filter=endpoint, date_filter=date_filter)
        
        return {
            "status": "success",
            "mapping_stats": mapping_stats,
            "consult_stats": consult_stats,
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

