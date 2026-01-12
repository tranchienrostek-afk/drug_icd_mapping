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
