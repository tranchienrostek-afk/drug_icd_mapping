from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app.monitor.service import get_system_stats
import os

router = APIRouter()

@router.get("/api/v1/monitor/stats")
async def get_stats():
    """
    Returns real-time system statistics.
    """
    return get_system_stats()

@router.get("/monitor", response_class=HTMLResponse)
async def monitor_dashboard():
    """
    Serves the simple monitoring dashboard.
    """
    # Read the HTML file directly instead of using Jinja2 to keep it simple and dependency-free
    file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content
