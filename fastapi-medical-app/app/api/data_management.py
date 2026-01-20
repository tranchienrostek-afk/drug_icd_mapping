
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.services import DrugDbEngine
from app.service.etl_service import process_raw_log
import uuid
import logging

router = APIRouter()
db = DrugDbEngine()
logger = logging.getLogger(__name__)

def run_etl_with_logging(batch_id: str, text_content: str):
    """Wrapper to catch and log ETL errors"""
    print(f"[DATA] BEFORE ETL execution for batch: {batch_id}", flush=True)
    try:
        print(f"[DATA] Starting ETL for batch: {batch_id}, content length: {len(text_content)}", flush=True)
        logger.info(f"[DATA] Starting ETL for batch: {batch_id}")
        
        # Import here to be safe
        from app.service.etl_service import process_raw_log
        stats = process_raw_log(batch_id, text_content)
        
        print(f"[DATA] ETL completed for batch {batch_id}: {stats}", flush=True)
        logger.info(f"[DATA] ETL completed for batch {batch_id}: {stats}")
    except Exception as e:
        print(f"[DATA] ETL ERROR for batch {batch_id}: {e}", flush=True)
        logger.error(f"[DATA] ETL failed for batch {batch_id}: {e}", exc_info=True)
        import traceback
        traceback.print_exc()

@router.post("/ingest")
async def ingest_medical_logs(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Ingest CSV logs for Knowledge Base building.
    Format: CSV with columns 'Tên thuốc', 'Mã ICD (Chính)', etc.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        batch_id = str(uuid.uuid4())
        
        # 1. Log Raw (await async call)
        try:
            await db.log_raw_data(batch_id, text_content, "API_UPLOAD")
        except Exception as log_err:
            logger.warning(f"[DATA] Failed to log raw data: {log_err}")
        
        # 2. Trigger Background ETL with error handling
        background_tasks.add_task(run_etl_with_logging, batch_id, text_content)
        
        return {"status": "processing", "batch_id": batch_id, "message": "File received and ETL started."}
        
    except Exception as e:
        logger.error(f"[DATA] Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

