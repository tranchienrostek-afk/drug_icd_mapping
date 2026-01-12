# TEST SCENARIOS & RESULTS

## 1. Test Suite: Drug Identification (Hybrid DB + Web)
**Context:** Validate khả năng tìm kiếm từ Database nội bộ (ưu tiên) và Web Fallback.

### Active Test Cases
| ID | Input | Strategy Used | Expected Output | Status | Last Run |
|---|---|---|---|---|---|
| TC_01 | "Paracetamol 500mg" | Exact DB | Found (<0.1s) | ✅ PASS | 2026-01-09 |
| TC_02 | "Sufentanil" | Partial DB | Found (DataCore) | ✅ PASS | 2026-01-09 |
| TC_03 | "Paretamol" | Fuzzy (Typo) | Found (Corrected) | ✅ PASS | 2026-01-09 |
| TC_04 | "Tra Hoang Bach Phong" | Vector (Semantic) | Found (No Accent) | ✅ PASS | 2026-01-09 |
| TC_05 | "Thuoc khong ton tai" | Web Search | Empty/Suggestion | ✅ PASS | 2026-01-09 |

## 2. Known Issues (Bugs)
- **Resolved:**
  - **BUG-013:** Search chậm/timeout.
    - *Resolution:* Fixed by importing DataCore (65k records) and optimizing search algorithm (Task 022 + 018). Most queries now hit DB instantly.

## 3. Test Environment
- **Local:** Windows, Python 3.11.
- **Docker:** `fastapi-medical-app` container (Rebuilt with RapidFuzz).
- **Tools:** `python scripts/benchmark_search.py`.