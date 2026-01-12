import os
import time
import json
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from io import BytesIO

class LogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "logs_api")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def get_log_file(self):
        filename = f"{datetime.now().strftime('%d_%m_%Y')}_api.log"
        return os.path.join(self.log_dir, filename)

    async def set_body(self, request: Request, body: bytes):
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive

    async def dispatch(self, request: Request, call_next):
        # 1. Log Request
        start_time = time.time()
        
        # Read body (safely)
        try:
            body_bytes = await request.body()
            await self.set_body(request, body_bytes) # restore for next handler
            request_body = body_bytes.decode("utf-8") if body_bytes else ""
        except:
            request_body = "<Could not read body>"

        # 2. Call endpoint
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception case
            self.write_log(request, request_body, 500, f"Error: {e}", time.time() - start_time)
            raise e

        # 3. Read Response Body
        # We need to act differently based on response type. 
        # StreamingResponse is hard to log fully without memory impact, usually we skipped it or peeked.
        # But for JSON APIs, it's usually small.
        
        response_body = ""
        if isinstance(response, StreamingResponse):
            # Capture content by iterating the iterator, then reconstructing it
            # This is expensive for large files!
            # Heuristic: Only capture if content-type is json or text
            if "application/json" in response.media_type or "text/" in response.media_type:
                content = b""
                async for chunk in response.body_iterator:
                    content += chunk
                
                response_body = content.decode("utf-8", errors="ignore")
                
                # Re-create iterator for the actual response
                response.body_iterator = iter([content])
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
        except Exception as e:
            print(f"LogMiddleware Error: {e}")
