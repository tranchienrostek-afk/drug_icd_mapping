# Task 028: Implement OpenAI Token Tracking & Cost Monitoring

## Context
We are using Azure OpenAI heavily for the Search Agent and other features. To manage costs and monitor usage, we need a precise logging system that tracks every token consumed.

## Objective
Create a `TokenTrackingService` that intercepts or wraps all OpenAI calls (specifically from `mcp_agent` and any other direct calls) and logs usage to a daily JSON file.

## Requirements

### 1. Log File Location
- **Path**: `C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\app\logs\trace_token_openai\`
- **Filename Format**: `DD_MM_YYYY_total_tokens.json` (e.g., `12_01_2026_total_tokens.json`).

### 2. Data Structure (JSON)
The file should contain two main sections: `details` (list of calls) and `summary` (daily totals).

```json
{
  "date": "12-01-2026",
  "summary": {
    "total_calls": 15,
    "total_input_tokens": 5000,
    "total_output_tokens": 1000,
    "total_cost_usd": 0.00135,
    "currency": "USD"
  },
  "details": [
    {
      "timestamp": "2026-01-12T10:00:00",
      "context": "Search Agent - Ludox 200mg (Step 1)",
      "model": "gpt-4o-mini",
      "input_tokens": 500,
      "output_tokens": 100,
      "total_tokens": 600,
      "cost_usd": 0.000135
    }
  ]
}
```

### 3. Cost Formula (GPT-4o-mini assumption based on user notes)
- **Input**: $0.15 / 1,000,000 tokens
- **Output**: $0.60 / 1,000,000 tokens
- *Note: Make these configurable constants.*

### 4. Implementation Logic
- create `app/core/token_tracker.py`.
- Implement a singleton or static service `TokenTracker`.
- Add a method `log_usage(context, model, usage_object)`.
- **Integration**:
    - Hook into `patched_request_completion_task` in `agent_search_service.py` to capture `response.usage`.
    - Ensure it is thread-safe (file locking or atomic writes recommended, or just simple append if low concurrency).

## Definition of Done
- [ ] `TokenTracker` class implemented.
- [ ] Integration with `agent_search_service.py` complete.
- [ ] Daily JSON file is created and updated correctly.
- [ ] summary" updates correctly after each call.
