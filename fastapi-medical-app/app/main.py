from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import drugs, diseases, analysis, admin
import os

app = FastAPI(title="Medical API System", version="1.0.0")

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(drugs.router, prefix="/api/v1/drugs", tags=["Drugs"])
app.include_router(diseases.router, prefix="/api/v1/diseases", tags=["Diseases"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))