from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load env vars (Explicit path)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import drugs, diseases, analysis, admin, data_management, consult
from app.core.middleware import LogMiddleware
from app.monitor.middleware import CircuitBreakerMiddleware, ApiMonitorMiddleware
from app.monitor.router import router as monitor_router
from app.monitor.service import clean_old_logs, setup_monitor_logger
from app.mapping_drugs.router import router as mapping_router

app = FastAPI(title="Medical API System", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Circuit Breaker (First line of defense)
app.add_middleware(CircuitBreakerMiddleware)

# Register API Monitor (Logging & Stats)
app.add_middleware(ApiMonitorMiddleware)

# Register logging middleware
app.add_middleware(LogMiddleware)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(drugs.router, prefix="/api/v1/drugs", tags=["Drugs"])
app.include_router(diseases.router, prefix="/api/v1/diseases", tags=["Diseases"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(data_management.router, prefix="/api/v1/data", tags=["Data Management"])
app.include_router(consult.router, prefix="/api/v1", tags=["Consultation"])
app.include_router(monitor_router, tags=["Monitor"]) # Exposes /monitor and /monitor/stats
app.include_router(mapping_router, prefix="/api/v1/mapping", tags=["Claims Mapping"])

@app.on_event("startup")
async def startup_event():
    # 1. Setup Monitor Logging (logs to app/monitor/monitor_alerts.log)
    setup_monitor_logger()
    
    # 2. Clean old monitor logs
    # cleans app/monitor/*.log
    clean_old_logs(retention_days=3)

@app.get("/api/v1/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    from app.database.core import DatabaseCore
    
    db_status = "ok"
    try:
        # Use DatabaseCore to support both SQLite and Postgres
        core = DatabaseCore()
        conn = core.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": db_status,
        "services": {
            "drug_search": "available",
            "consultation": "available",
            "crawler": "available"
        }
    }

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))