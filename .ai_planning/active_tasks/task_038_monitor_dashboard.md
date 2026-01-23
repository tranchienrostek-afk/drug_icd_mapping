# Task 038: Lightweight Service Monitoring & Log Retention (Urgent)

**Status**: COMPLETED
**Priority**: CRITICAL
**Context**: Reports of server instability. Need urgent visibility into resource usage (RAM, CPU, Disk) and request load to verify if our service is the bottleneck.

## 1. Objectives
1.  **Real-time Monitoring**: Visual dashboard (HTML) for CPU, RAM, Disk, and Request Rate.
2.  **Resource Safety**: Ensure logs are rotated every 3 days to prevent disk overflow.
3.  **Simplicity**: No complex stacks (Prometheus/Grafana) for now. Just Python + HTML.

## 2. Implementation Plan

### Phase 1: Backend Metrics Endpoint
-   **Directory**: `app/monitor/` (Self-contained module)
-   **Library**: Add `psutil` to `requirements.txt`.
-   **Files**:
    -   `app/monitor/service.py`: Wrapper for `psutil` to get safe stats.
    -   `app/monitor/router.py`: API Endpoints.

### Phase 2: Resource Circuit Breaker (Auto-Protection)
-   **File**: `app/monitor/middleware.py` (Circuit Breaker Logic)
-   **Logic**:
    -   Check RAM/CPU on every request.
    -   **Thresholds** (Configurable in `.env`):
        -   `MAX_RAM_PERCENT`: Default 90%
        -   `MAX_CPU_PERCENT`: Default 95%
    -   **Action**: If exceeded -> Return `503 Service Unavailable`.
    -   **Logging**: Log a `CRITICAL` alert with current stats: "Server Overload: RAM 92% > 90%. Rejecting request."

### Phase 3: Simple Monitoring Dashboard
-   **File**: `app/monitor/static/index.html`
-   **Endpoint**: `GET /monitor` (Serves the HTML)
-   **Tech**: Plain HTML + Vanilla JS + Simple CSS.
-   **Features**:
    -   Auto-refresh every 3 seconds.
    -   Color-coded indicators (Green/Yellow/Red) for resource usage.
    -   Display uptime and basic service status.
-   **Security**: Protect with a simple static token or Basic Auth (optional for now, but recommended).

### Phase 3: Log Retention Policy (3 Days)
-   **Configuration**: Update Logging Config (likely in `app/core/config.py` or `main.py`).
-   **Mechanism**:
    -   Use `TimedRotatingFileHandler` or `loguru`'s rotation feature.
    -   Settings: `rotation="00:00"`, `retention="3 days"`.

## 3. Execution Steps
1.  [ ] Create `task_038_monitoring_dashboard.md` (This file).
2.  [ ] Add `psutil` to `requirements.txt`.
3.  [ ] Implement `/monitor/stats` endpoint.
4.  [ ] Create `monitor.html`.
5.  [ ] Configure Log Retention.
6.  [ ] Verify on Local Docker.
7.  [ ] Deploy to Remote Server (Hotfix).

## 4. Verification
-   **Local**: Run `docker-compose up`, access `http://localhost:8000/static/monitor.html`.
-   **Remote**: Access `http://10.14.190.28:8000/static/monitor.html` and observe metrics.
