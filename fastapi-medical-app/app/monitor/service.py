import psutil
import shutil
import os
import time
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

MONITOR_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(MONITOR_DIR, "monitor.db")

def init_db():
    """Initializes the SQLite database for monitoring."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            request_id TEXT,
            endpoint TEXT,
            method TEXT,
            status_code INTEGER,
            latency_ms REAL,
            matched_count INTEGER DEFAULT 0,
            unmatched_count INTEGER DEFAULT 0,
            request_body TEXT,
            response_body TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize DB on module load
init_db()

def log_api_request(
    request_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    latency_ms: float,
    matched_count: int = 0,
    unmatched_count: int = 0,
    request_body: str = "",
    response_body: str = ""
):
    """Logs an API request to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO request_logs 
            (request_id, endpoint, method, status_code, latency_ms, matched_count, unmatched_count, request_body, response_body)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (request_id, endpoint, method, status_code, latency_ms, matched_count, unmatched_count, request_body, response_body))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.getLogger("monitor").error(f"Failed to log request to DB: {e}")

def get_monitor_stats():
    """Returns summary stats for the dashboard."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Requests per endpoint
        cursor.execute("SELECT endpoint, COUNT(*) as count FROM request_logs GROUP BY endpoint")
        endpoint_stats = {row['endpoint']: row['count'] for row in cursor.fetchall()}
        
        # Recent trends (last 24h)
        # ... logic if needed
        
        conn.close()
        return {
            "endpoints": endpoint_stats,
            "system": get_system_stats()
        }
    except Exception as e:
        return {"error": str(e)}

def get_recent_logs(limit: int = 100, endpoint_filter: str = None, date_filter: str = None):
    """Returns the most recent request logs with optional filters."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM request_logs WHERE 1=1"
        params = []
        
        if endpoint_filter:
            query += " AND endpoint LIKE ?"
            params.append(f"%{endpoint_filter}%")
        
        if date_filter:
            if date_filter == "today":
                query += " AND date(timestamp) = date('now')"
            elif date_filter == "week":
                query += " AND timestamp >= datetime('now', '-7 days')"
            elif date_filter == "month":
                query += " AND timestamp >= datetime('now', '-30 days')"
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    except Exception as e:
        return []

def get_api_detailed_stats(endpoint: str = None, date_filter: str = None):
    """Returns detailed stats including success/failure rates."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        where_clause = "WHERE 1=1"
        params = []
        
        if endpoint:
            where_clause += " AND endpoint LIKE ?"
            params.append(f"%{endpoint}%")
        
        if date_filter:
            if date_filter == "today":
                where_clause += " AND date(timestamp) = date('now')"
            elif date_filter == "week":
                where_clause += " AND timestamp >= datetime('now', '-7 days')"
            elif date_filter == "month":
                where_clause += " AND timestamp >= datetime('now', '-30 days')"
        
        # Total counts
        cursor.execute(f"SELECT COUNT(*) as total FROM request_logs {where_clause}", params)
        total = cursor.fetchone()['total']
        
        cursor.execute(f"SELECT COUNT(*) as success FROM request_logs {where_clause} AND status_code < 400", params)
        success = cursor.fetchone()['success']
        
        cursor.execute(f"SELECT COUNT(*) as failure FROM request_logs {where_clause} AND status_code >= 400", params)
        failure = cursor.fetchone()['failure']
        
        # Matched/Unmatched totals
        cursor.execute(f"SELECT SUM(matched_count) as total_matched, SUM(unmatched_count) as total_unmatched FROM request_logs {where_clause}", params)
        row = cursor.fetchone()
        total_matched = row['total_matched'] or 0
        total_unmatched = row['total_unmatched'] or 0
        
        # Average latency
        cursor.execute(f"SELECT AVG(latency_ms) as avg_latency FROM request_logs {where_clause}", params)
        avg_latency = cursor.fetchone()['avg_latency'] or 0
        
        conn.close()
        
        success_rate = round((success / total) * 100, 1) if total > 0 else 100.0
        coverage_rate = round((total_matched / (total_matched + total_unmatched)) * 100, 1) if (total_matched + total_unmatched) > 0 else 0
        
        return {
            "total_requests": total,
            "success_count": success,
            "failure_count": failure,
            "success_rate": success_rate,
            "total_matched": total_matched,
            "total_unmatched": total_unmatched,
            "coverage_rate": coverage_rate,
            "avg_latency_ms": round(avg_latency, 0)
        }
    except Exception as e:
        return {"error": str(e)}

def clean_old_logs(log_dir: str = MONITOR_DIR, retention_days: int = 3):
    """
    Deletes log files in log_dir (default app/monitor) older than retention_days.
    """
    if not os.path.exists(log_dir):
        return

    cutoff_time = time.time() - (retention_days * 86400)
    
    for filename in os.listdir(log_dir):
        if not filename.endswith(".log"): 
            continue
            
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                except Exception:
                    pass

def setup_monitor_logger():
    # ... (existing code rest unchanged or slightly modified)
    logger = logging.getLogger("monitor")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        log_file = os.path.join(MONITOR_DIR, "monitor_alerts.log")
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def get_system_stats():
    """Returns basic system stats for the dashboard summary."""
    sys_cpu = psutil.cpu_percent(interval=None)
    virtual_mem = psutil.virtual_memory()
    disk_usage = shutil.disk_usage("/")
    process = psutil.Process()
    try:
        proc_cpu = process.cpu_percent(interval=None)
        proc_mem = process.memory_info().rss
    except Exception:
        proc_cpu = 0
        proc_mem = 0
    return {
        "cpu": sys_cpu,
        "ram": {"percent": virtual_mem.percent, "used": virtual_mem.used, "total": virtual_mem.total},
        "disk": {"percent": (disk_usage.used / disk_usage.total) * 100 if disk_usage.total > 0 else 0},
        "process": {"cpu": proc_cpu, "ram": proc_mem}
    }


def get_detailed_system_stats():
    """Returns comprehensive system hardware information."""
    sys_cpu = psutil.cpu_percent(interval=0.5)
    virtual_mem = psutil.virtual_memory()
    disk_usage = shutil.disk_usage("/")
    net_io = psutil.net_io_counters()
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    
    # CPU frequency (may not be available on all systems)
    cpu_freq = None
    try:
        freq = psutil.cpu_freq()
        if freq:
            cpu_freq = {"current": freq.current, "min": freq.min, "max": freq.max}
    except Exception:
        pass
    
    # Process (this app) stats
    process = psutil.Process()
    try:
        proc_cpu = process.cpu_percent(interval=None)
        proc_mem = process.memory_info().rss
        proc_threads = process.num_threads()
    except Exception:
        proc_cpu = 0
        proc_mem = 0
        proc_threads = 0
    
    return {
        "cpu": {
            "percent": sys_cpu,
            "count": psutil.cpu_count(),
            "count_logical": psutil.cpu_count(logical=True),
            "frequency": cpu_freq
        },
        "memory": {
            "total": virtual_mem.total,
            "available": virtual_mem.available,
            "used": virtual_mem.used,
            "percent": virtual_mem.percent
        },
        "disk": {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "percent": (disk_usage.used / disk_usage.total) * 100 if disk_usage.total > 0 else 0
        },
        "network": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        },
        "uptime": {
            "boot_time": boot_time,
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": _format_uptime(uptime_seconds)
        },
        "process": {
            "cpu": proc_cpu,
            "ram": proc_mem,
            "threads": proc_threads
        }
    }


def _format_uptime(seconds: float) -> str:
    """Format uptime in human readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def check_resources(max_cpu: float, max_ram: float) -> tuple[bool, str]:
    """Check if resources are within acceptable limits."""
    cpu_percent = psutil.cpu_percent(interval=None)
    ram_percent = psutil.virtual_memory().percent
    if cpu_percent > max_cpu:
        return False, f"CPU Critical: {cpu_percent}% > {max_cpu}%"
    if ram_percent > max_ram:
        return False, f"RAM Critical: {ram_percent}% > {max_ram}%"
    return True, "OK"

