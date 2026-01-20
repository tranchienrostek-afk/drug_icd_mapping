from datetime import datetime, timedelta
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, status, Depends
from app.services import DrugDbEngine
from app.service.etl_service import process_raw_log
import uuid
import logging

router = APIRouter()
db = DrugDbEngine()
logger = logging.getLogger(__name__)

# Rate Limiting State (In-Memory)
LAST_INGEST_TIME = None
COOLDOWN_TIMEDELTA = timedelta(minutes=2)

def check_ingest_rate_limit():
    """
    Enforce 1 request per 2 minutes for ingest API.
    Raises 429 if cooldown has not passed.
    """
    global LAST_INGEST_TIME
    now = datetime.now()
    
    if LAST_INGEST_TIME and (now - LAST_INGEST_TIME) < COOLDOWN_TIMEDELTA:
        remaining = COOLDOWN_TIMEDELTA - (now - LAST_INGEST_TIME)
        reason = f"Rate limit exceeded. Please wait {int(remaining.total_seconds())} seconds."
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason
        )
    
    # Update time immediately upon acceptance (simple leaky bucket)
    LAST_INGEST_TIME = now

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

@router.post("/ingest", dependencies=[Depends(check_ingest_rate_limit)])
async def ingest_medical_logs(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Ingest CSV logs for Knowledge Base building.
    Format: CSV with columns 'Tên thuốc', 'Mã ICD (Chính)', etc.
    Rate Limit: 1 request every 2 minutes.
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

