from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE
from starlette.responses import StreamingResponse
from app.monitor.service import check_resources, log_api_request
import logging
import os
import time
import json

# Configure logging for the monitor
monitor_logger = logging.getLogger("monitor")

class ApiMonitorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.tracked_endpoints = [
            "/api/v1/consult_integrated",
            "/api/v1/mapping/match",
            "/api/v1/mapping/match_v2"
        ]

    async def dispatch(self, request: Request, call_next):
        if request.url.path not in self.tracked_endpoints:
            return await call_next(request)

        start_time = time.time()
        
        # 1. Call endpoint WITHOUT reading request body to avoid ASGI issues
        try:
            response = await call_next(request)
        except Exception as e:
            # We don't have the request body here, but it's better than crashing
            monitor_logger.error(f"Middleware call_next failed: {e}")
            raise e

        # 2. Capture response body - handle different response types
        response_body_bytes = b""
        
        # StreamingResponse needs special handling - consume and recreate iterator
        if isinstance(response, StreamingResponse):
            content = b""
            async for chunk in response.body_iterator:
                content += chunk
            response_body_bytes = content
            
            # Recreate iterator so client still gets data
            async def body_generator():
                yield content
            response.body_iterator = body_generator()
        
        # Regular Response with body attribute
        elif hasattr(response, "body"):
            response_body_bytes = response.body
        
        # JSONResponse or other types - try to get body
        elif hasattr(response, "body_iterator"):
            try:
                content = b""
                async for chunk in response.body_iterator:
                    content += chunk
                response_body_bytes = content
                
                # Recreate iterator
                async def body_gen():
                    yield content
                response.body_iterator = body_gen()
            except Exception:
                pass

        latency_ms = (time.time() - start_time) * 1000
        
        # 3. Parse for stats and request_id from RESPONSE
        matched_count = 0
        unmatched_count = 0
        request_id = ""
        
        try:
            resp_str = response_body_bytes.decode("utf-8", errors="ignore")
            resp_json = json.loads(resp_str)
            
            # Extract request_id from response if available
            request_id = resp_json.get("request_id", "")
            
            if "/consult_integrated" in request.url.path:
                results = resp_json.get("results", [])
                matched_count = sum(1 for r in results if r.get("category") == "drug" and r.get("validity") == "valid")
                unmatched_count = len(results) - matched_count
            elif "/mapping/match" in request.url.path: # covers match and match_v2
                summary = resp_json.get("summary", {})
                matched_count = summary.get("matched_items", 0)
                unmatched_count = summary.get("unmatched_claims", 0)
        except Exception:
            pass 

        # 4. Log to DB
        try:
            log_api_request(
                request_id=request_id,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                latency_ms=latency_ms,
                matched_count=matched_count,
                unmatched_count=unmatched_count,
                request_body="<Not captured for performance/stability>",
                response_body=response_body_bytes.decode("utf-8", errors="ignore")[:100000]
            )
        except Exception as e:
            monitor_logger.error(f"ApiMonitorMiddleware logging error: {e}")
        
        return response

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.max_cpu = float(os.getenv("MONITOR_MAX_CPU", "95.0"))
        # User requested to allow 100% RAM usage for weak machine
        self.max_ram = float(os.getenv("MONITOR_MAX_RAM", "100.0"))
        self.whitelist_paths = ["/monitor", "/api/v1/monitor/stats", "/api/v1/monitor/logs", "/static"]

    async def dispatch(self, request: Request, call_next):
        # Skip check for monitor endpoints so admin can still see status
        if any(request.url.path.startswith(path) for path in self.whitelist_paths):
            return await call_next(request)

        # Check Resources
        is_safe, message = check_resources(self.max_cpu, self.max_ram)
        
        if not is_safe:
            monitor_logger.critical(f"CIRCUIT BREAKER TRIGGERED: {message}. Rejecting request to {request.url.path}")
            return Response(
                content=f"Service Temporarily Unavailable due to High Load. {message}",
                status_code=HTTP_503_SERVICE_UNAVAILABLE
            )

        return await call_next(request)
