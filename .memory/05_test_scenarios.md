# TEST SCENARIOS & RESULTS

## 1. Test Suite: Drug Identification (Crawler)
**Context:** Validate khả năng tìm kiếm và trích xuất thông tin thuốc từ web.

### Active Test Cases
| ID | Input | Expected Output | Status | Last Run |
|---|---|---|---|---|
| TC_01 | "Paracetamol" | SDK found, Active Ingredient: Paracetamol | PASS | 2026-01-08 |
| TC_02 | "Symbicort" | SDK: VN-17730-14 | PASS (Local) | 2026-01-08 |
| TC_03 | "Ludox" | SDK found | FAIL (Timeout) | 2026-01-08 |
| TC_04 | "RandomStringXYZ" | Empty Result (Handled Gracefully) | PASS | 2026-01-07 |

## 2. Known Issues (Bugs)
- **BUG-013:** Search chậm và timeout với danh sách 5 thuốc (Ludox, Althax...).
  - *Root Cause:* Google Search API rate limit & Internal search Slowness.
  - *Status:* In-Progress (Task 017).

## 3. Test Environment
- **Local:** Windows, Python 3.10.
- **Docker:** `fastapi-medical-app` container.
- **Tools:** `pytest`, `scripts/test_bug_013.py`.