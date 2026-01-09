# TASK TICKET: [TASK_018] - [Optimize Search Algorithm & Fuzzy Matching]

**Status:** In Progress
**Priority:** High
**Người Tạo:** AI Scientist
**Ngày tạo:** 09.01.2026

**Linked to:** `task_022_import_datacore.md`

---

## 1. Mục tiêu (Objective)
Nâng cấp "trí tuệ" của bộ máy tìm kiếm để xử lý tốt hơn các trường hợp:
1.  **Lỗi chính tả (Typos):** Input "Paretamol" phải tìm ra "Paracetamol" (Fuzzy Matching).
2.  **Semantic Search:** Input "Tra Hoang Bach Phong" phải tìm ra thuốc trong DB dù format khác nhau (Vector Search).
3.  **Performance:** Giảm thiểu việc phải fallback sang Web Search (chậm) bằng cách tăng hit-rate trong DB.

---

## 2. Implementation Plan

### Step 1: Dependencies & Configuration
- Thêm thư viện `rapidfuzz` vào `requirements.txt`.
- Tune Threshold Vector Search: Giảm từ **0.85** xuống **0.75** (hoặc **0.70** sau khi test).

### Step 2: Search Index Optimization
- **Problem:** Hiện tại `search_text` bao gồm cả SDK ("VD-...", "VN-..."). Khi user search tên ngắn, tỷ lệ khớp (TF-IDF) bị giảm do SDK làm "loãng" vector.
- **Solution:** Loại bỏ SDK khỏi `search_text`. Chỉ giữ lại `Tên thuốc` + `Hoạt chất` (Normalized). SDK sẽ được search bằng query SQL riêng biệt.
- **Action:** Sửa `run_import_datacore.py` và chạy lại chế độ Update.

### Step 3: Implement RapidFuzz Logic
- Sửa `app/services.py` -> `search_drug_smart`.
- Thêm bước **Fuzzy Match** (Levenshtein distance) vào pipeline:
  ```python
  # Pipeline mới:
  1. Exact Match (SQL)
  2. SDK Match (Regex + SQL)
  3. Fuzzy Match (RapidFuzz > 90%) -> New!
  4. Vector Search (TF-IDF > 0.75)
  5. Web Search (Fallback)
  ```

---

## 3. Acceptance Criteria
| Case | Input | Expected Behavior | Current |
|---|---|---|---|
| **Typo** | "Paretamol" | Found in DB (Fuzzy) | Web Search (Slow) |
| **Vector** | "Tra Hoang Bach Phong" | Found in DB (Vector) | Web Search (Slow) |
| **Speed** | Above cases | < 1s | > 30s |

---
