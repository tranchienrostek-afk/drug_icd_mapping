from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app.monitor.service import get_system_stats, get_monitor_stats, get_recent_logs
import os

router = APIRouter()

@router.get("/api/v1/monitor/stats")
async def get_summary_stats():
    """
    Returns summary statistics for the monitoring dashboard.
    """
    return get_monitor_stats()

@router.get("/api/v1/monitor/logs")
async def get_detailed_logs(limit: int = 50):
    """
    Returns the most recent detailed request logs.
    """
    return get_recent_logs(limit=limit)

@router.get("/monitor", response_class=HTMLResponse)
async def monitor_dashboard():
    """
    Serves the advanced monitoring dashboard.
    """
    file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if not os.path.exists(file_path):
        return "<h1>Dashboard UI Not Found</h1><p>Please ensure app/monitor/static/index.html is created.</p>"
        
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content
