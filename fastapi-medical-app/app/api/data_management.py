
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.services import DrugDbEngine
from app.service.etl_service import process_raw_log
import uuid

router = APIRouter()
db = DrugDbEngine()

@router.post("/ingest")
async def ingest_medical_logs(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Ingest CSV logs for Knowledge Base building.
    Format: CSV with columns 'drug_name', 'disease_name', 'icd_code' (optional).
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        batch_id = str(uuid.uuid4())
        
        # 1. Log Raw
        db.log_raw_data(batch_id, text_content, "API_UPLOAD")
        
        # 2. Trigger Background ETL
        background_tasks.add_task(process_raw_log, batch_id, text_content)
        
        return {"status": "processing", "batch_id": batch_id, "message": "File received and ETL started."}
        
    except Exception as e:
        # Log error?
        raise HTTPException(status_code=500, detail=str(e))
