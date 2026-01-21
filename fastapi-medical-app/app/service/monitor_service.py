from datetime import datetime, timedelta
import logging
import sqlite3
import json
from app.database.core import DatabaseCore

logger = logging.getLogger(__name__)

class MonitorService:
    def __init__(self, db_core: DatabaseCore):
        self.db_core = db_core

    def log_api_request(self, endpoint: str, method: str, status_code: int, response_time_ms: float, client_ip: str):
        """
        Log an API request to the database.
        """
        try:
            conn = self.db_core.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_logs (endpoint, method, status_code, response_time_ms, client_ip)
                VALUES (?, ?, ?, ?, ?)
            """, (endpoint, method, status_code, response_time_ms, client_ip))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")

    def get_ingestion_stats(self, limit: int = 50):
        """
        Get stats about ingestion batches from knowledge_base.
        Since we don't have a separate batches table, we aggregate from knowledge_base.
        """
        conn = self.db_core.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Group by batch_id
            cursor.execute("""
                SELECT 
                    batch_id,
                    COUNT(*) as total_rows,
                    MIN(last_updated) as started_at,
                    MAX(last_updated) as completed_at,
                    COUNT(DISTINCT drug_name_norm) as unique_drugs,
                    COUNT(DISTINCT disease_icd) as unique_diseases
                FROM knowledge_base
                WHERE batch_id IS NOT NULL
                GROUP BY batch_id
                ORDER BY completed_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_api_stats(self, days: int = 1):
        """
        Get API Health stats for the last N days.
        """
        conn = self.db_core.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Filter usually for consult endpoint
            endpoint_filter = "/api/v1/consult_integrated"
            
            stats = {}
            
            # 1. Total Requests
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM api_logs 
                WHERE endpoint LIKE ? AND created_at >= datetime('now', ?)
            """, (f"%{endpoint_filter}%", f"-{days} days"))
            stats['total_requests'] = cursor.fetchone()['total']
            
            # 2. Success Rate
            cursor.execute("""
                SELECT COUNT(*) as errors 
                FROM api_logs 
                WHERE endpoint LIKE ? AND status_code >= 500 AND created_at >= datetime('now', ?)
            """, (f"%{endpoint_filter}%", f"-{days} days"))
            errors = cursor.fetchone()['errors']
            
            if stats['total_requests'] > 0:
                stats['success_rate'] = round(((stats['total_requests'] - errors) / stats['total_requests']) * 100, 2)
            else:
                stats['success_rate'] = 100.0
                
            # 3. Avg Latency
            cursor.execute("""
                SELECT AVG(response_time_ms) as avg_latency
                FROM api_logs 
                WHERE endpoint LIKE ? AND created_at >= datetime('now', ?)
            """, (f"%{endpoint_filter}%", f"-{days} days"))
            avg = cursor.fetchone()['avg_latency']
            stats['avg_latency'] = round(avg, 2) if avg else 0
            
            # 4. Recent Logs
            cursor.execute("""
                SELECT * FROM api_logs
                WHERE endpoint LIKE ?
                ORDER BY created_at DESC
                LIMIT 20
            """, (f"%{endpoint_filter}%",))
            stats['recent_logs'] = [dict(r) for r in cursor.fetchall()]

            return stats
        finally:
            conn.close()
