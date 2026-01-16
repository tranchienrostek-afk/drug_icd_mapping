from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import drugs, diseases, analysis, admin, data_management, consult
from app.core.middleware import LogMiddleware
import os

app = FastAPI(title="Medical API System", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/v1/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    import sqlite3
    import os
    
    db_path = os.getenv("DB_PATH", "app/database/medical.db")
    db_status = "ok"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
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