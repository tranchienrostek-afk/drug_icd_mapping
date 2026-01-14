# Task 027: Integrate Search Agent to Server (FastAPI)

## Context
We have successfully tested the `Browser MCP Agent` locally using a CLI runner (`task_26_search_runner.py`). The agent can now exhaustively search for drug information (specifically bypassing Google blocking by using direct sites like ThuocBietDuoc).
Now, the user wants to "build to server".

## Objective
Migrate the proven local search logic into the `fastapi-medical-app` structure and ensure it can run within the Docker environment.

## Requirements
1.  **Code Migration**:
    -   Move logic from `task_26_search_runner.py` to `fastapi-medical-app/app/services/agent_search_service.py` (or similar).
    -   Refactor `SessionState` (which was for CLI/Streamlit simulation) to a proper class based structure or stateless function.
    -   Ensure `patched_request_completion_task` (Azure OpenAI fix) is properly integrated into the app's configuration.

2.  **Dependencies**:
    -   Update `fastapi-medical-app/requirements.txt` to include `mcp-agent`, `playwright`, `azure-openai`.
    -   Ensure `Dockerfile` installs Playwright browsers (`RUN playwright install --with-deps chromium`).

3.  **API Integration**:
    -   Create an endpoint (e.g., `POST /api/v1/search/agent`) that triggers the agent workflow.
    -   Accept `query` (drug name) as input.
    -   Return the JSON result.

4.  **Verification**:
    -   Build the Docker container.
    -   Run the container.
    -   Test the endpoint with "Ludox - 200mg" to confirm it works in the containerized environment.

## Definition of Done
- [ ] Code ported to `fastapi-medical-app`.
- [ ] `Dockerfile` updated a rebuilt successfully.
- [ ] Server starts without errors.
- [ ] Test request returns valid JSON drug info.

## **STATUS**: ⚠️ BLOCKED (Server Crashing)
**Last Update**: 2026-01-12
**Current Blocker**: `AsyncAzureOpenAI` integration or Playwright initialization is causing the Uvicorn worker to crash silently ("Connection aborted") inside Docker. Configuration issues (API Keys, Model Names) have been resolved.

## Findings & Decisions
- **Azure Integration**:
  - Requires `api-version=2024-06-01` (or newer) for `gpt-4o-mini`.
  - Library `mcp-agent` sends `parallel_tool_calls` by default, which Azure rejects with `400 Bad Request`. Fix: Explicitly remove this key from payload.
  - Environment variables must be carefully aligned: `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` vs `AZURE_OPENAI_DEPLOYMENT_NAME`.
- **Infrastructure**:
  - Docker container was missing `OPENAI_API_KEY` (required by library internals) and `AZURE_OPENAI_API_KEY` due to `.env` encoding issues. Fixed by cleaning file.
- **Critical Issue**: Server process crashes (SEGFAULT or OOM likely) during Agent execution, even when LLM response is mocked. Suspect Playwright initialization in Docker environment.
