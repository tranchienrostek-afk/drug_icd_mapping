from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE
from app.monitor.service import check_resources
import logging
import os

# Configure logging for the monitor
monitor_logger = logging.getLogger("monitor")

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.max_cpu = float(os.getenv("MONITOR_MAX_CPU", "95.0"))
        self.max_ram = float(os.getenv("MONITOR_MAX_RAM", "90.0"))
        self.whitelist_paths = ["/monitor", "/api/v1/monitor/stats", "/static"]

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
