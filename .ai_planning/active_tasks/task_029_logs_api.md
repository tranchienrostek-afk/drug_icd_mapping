# Task 029: Implement Global API Logging Middleware

## Context
To debug issues and audit usage, we need to record the payload (Body/Query) and Response of every API call handled by the FastAPI server.

## Objective
Implement a `LogMiddleware` in FastAPI that intercepts every request, reads the body, executes the request, reads the response, and writes everything to a daily log file.

## Requirements

### 1. Log File Location
- **Path**: `C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\app\logs\logs_api\`
- **Filename Format**: `DD_MM_YYYY_api.log` (e.g., `12_01_2026_api.log`).

### 2. Log Format
The logs should be human-readable or structured JSON lines (JSONL preferred for parsing, but user said "ghi vào ... theo ngày" simply). Let's use a structured text block for readability:

```text
[2026-01-12 10:05:00] [POST] /api/v1/drugs/agent-search
Client: 127.0.0.1
Request Body:
{
  "drugs": ["Ludox - 200mg"]
}
Status Code: 200 OK
Response Body:
{
  "results": [ ... ]
}
Duration: 15.2s
--------------------------------------------------
```

### 3. Implementation Details
- Create `app/middlewares/logging_middleware.py`.
- Use `Starlette` middleware pattern (FastAPI base).
- **Challenge**: Reading the request body consumes the stream. Need to use `await request.body()` and then re-inject it so the actual route handler can read it again.
- **Challenge**: Capturing Response body requires wrapping the `call_next` response iterator.

### 4. Configuration
- Ensure sensitive data (passwords, keys) is masked if any (currently mostly public drug data, so low risk).
- Create the directory if it doesn't exist.

## Definition of Done
- [ ] Middleware created and registered in `app/main.py`.
- [ ] Requests to `/api/v1/*` result in entries in the log file.
- [ ] Both Request JSON and Response JSON are visible.
- [ ] Timestamps and Duration are recorded.
