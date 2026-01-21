import os
import time
import json
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from io import BytesIO

from app.database.core import DatabaseCore
from app.service.monitor_service import MonitorService

class LogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        
        # Initialize Monitor Service for DB Logging
        try:
            # We use a default path or env var. 
            # Note: Middleware init happens on startup.
            db_path = os.getenv("DB_PATH", "app/database/medical.db")
            self.db_core = DatabaseCore(db_path)
            self.monitor_service = MonitorService(self.db_core)
        except Exception as e:
            print(f"LogMiddleware Warning: Could not init MonitorService: {e}")
            self.monitor_service = None

        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "logs_api")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def get_log_file(self):
        filename = f"{datetime.now().strftime('%d_%m_%Y')}_api.log"
        return os.path.join(self.log_dir, filename)

    async def set_body(self, request: Request, body: bytes):
        """
        Restore the request body after reading it.
        Creates a proper ASGI receive callable that handles both request body and disconnect.
        """
        body_sent = False
        
        async def receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            # After body is sent, return disconnect on subsequent calls
            return {"type": "http.disconnect"}
        
        request._receive = receive

    async def dispatch(self, request: Request, call_next):
        # 1. Log Request
        start_time = time.time()
        
        # IMPORTANT: Do NOT read request body here to avoid ASGI issues.
        # We will log the body only for specific content types and only if needed.
        request_body = ""
        
        # Check if it's a POST/PUT/PATCH with JSON body
        content_type = request.headers.get("content-type", "")
        if request.method in ("POST", "PUT", "PATCH") and "application/json" in content_type:
            # For logging purposes, we can try to read the body BUT it may cause issues.
            # Instead, we'll just log that there was a JSON body without reading it.
            request_body = "<JSON body - not captured to avoid ASGI issues>"
        
        # 2. Call endpoint
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception case
            self.write_log(request, request_body, 500, f"Error: {e}", time.time() - start_time)
            raise e

        # 3. Read Response Body (only for JSON responses)
        response_body = ""
        if isinstance(response, StreamingResponse):
            media_type = response.media_type or ""
            if "application/json" in media_type or "text/" in media_type:
                content = b""
                async for chunk in response.body_iterator:
                    content += chunk
                
                response_body = content.decode("utf-8", errors="ignore")
                
                # Re-create iterator for the actual response - use async generator
                async def body_generator():
                    yield content
                response.body_iterator = body_generator()
            else:
                response_body = "<Binary/Stream content>"
        else:
             # Standard response
             if hasattr(response, "body"):
                 response_body = response.body.decode("utf-8", errors="ignore")

        # 4. Write Log
        duration = time.time() - start_time
        self.write_log(request, request_body, response.status_code, response_body, duration)

        return response

    def write_log(self, request, req_body, status, res_body, duration):
        # Filter: Skip static files or simple health checks if needed
        if "/static" in request.url.path:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] [{request.method}] {request.url.path}\n"
            f"Client: {request.client.host if request.client else 'Unknown'}\n"
            f"Duration: {duration:.3f}s\n"
            f"Status: {status}\n"
            f"Request Body:\n{req_body}\n"
            f"Response Body:\n{res_body}\n"
            f"--------------------------------------------------\n"
        )
        
        try:
            with open(self.get_log_file(), "a", encoding="utf-8") as f:
                f.write(log_entry)
            
            # DB Logging via MonitorService (Async safe?)
            # Since this is sync method, we just call it. MonitorService is sync for now (uses DB core).
            if self.monitor_service:
                # Log everything except health checks and static
                if request.url.path.startswith("/api/") and "/health" not in request.url.path:
                    client_ip = request.client.host if request.client else 'Unknown'
                    self.monitor_service.log_api_request(
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=status,
                        response_time_ms=duration * 1000, # convert to ms
                        client_ip=client_ip
                    )
        except Exception as e:
            print(f"LogMiddleware Error: {e}")
