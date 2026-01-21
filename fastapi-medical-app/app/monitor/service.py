import psutil
import shutil
import os
import time
import logging
from datetime import datetime, timedelta

MONITOR_DIR = os.path.dirname(os.path.abspath(__file__))

def setup_monitor_logger():
    """Configures the 'monitor' logger to write to app/monitor/monitor.log"""
    logger = logging.getLogger("monitor")
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if called multiple times
    if not logger.handlers:
        log_file = os.path.join(MONITOR_DIR, "monitor_alerts.log")
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def clean_old_logs(log_dir: str = MONITOR_DIR, retention_days: int = 3):
    """
    Deletes log files in log_dir (default app/monitor) older than retention_days.
    """
    if not os.path.exists(log_dir):
        return

    cutoff_time = time.time() - (retention_days * 86400)
    
    # Clean standard logs and our specific monitor logs if rotated
    for filename in os.listdir(log_dir):
        if not filename.endswith(".log"): 
            continue
            
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            # Check modification time
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    print(f"Deleted old log file: {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")

def get_system_stats():
    """
    Returns current system AND process statistics:
    - CPU Usage (System % vs Process %)
    - RAM Usage (System Total, Process Used)
    """
    # 1. System Stats
    sys_cpu = psutil.cpu_percent(interval=None)
    virtual_mem = psutil.virtual_memory()
    disk_usage = shutil.disk_usage("/")
    
    # 2. Process Stats (The FastAPI App)
    process = psutil.Process()
    try:
        # functionality availability varies by OS
        proc_cpu = process.cpu_percent(interval=None)
        proc_mem = process.memory_info().rss # Resident Set Size (Physical Memory)
    except Exception:
        proc_cpu = 0
        proc_mem = 0

    return {
        "system": {
            "cpu": sys_cpu,
            "ram": {
                "total": virtual_mem.total,
                "percent": virtual_mem.percent,
                "used": virtual_mem.used,
                "free": virtual_mem.free
            },
            "disk": {
                "percent": (disk_usage.used / disk_usage.total) * 100 if disk_usage.total > 0 else 0
            }
        },
        "process": {
            "cpu": proc_cpu,
            "ram": proc_mem # Bytes
        }
    }

def check_resources(max_cpu: float, max_ram: float) -> tuple[bool, str]:
    """
    Checks if resources are within safe limits.
    Returns: (is_safe: bool, message: str)
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    ram_percent = psutil.virtual_memory().percent

    if cpu_percent > max_cpu:
        return False, f"CPU Critical: {cpu_percent}% > {max_cpu}%"
    
    if ram_percent > max_ram:
        return False, f"RAM Critical: {ram_percent}% > {max_ram}%"
    
    return True, "OK"
