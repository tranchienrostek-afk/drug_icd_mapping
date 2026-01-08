# TASK TICKET: [TASK_ID] - [TÊN TASK NGẮN GỌN]
**Status:** Todo / In Progress
**Linked to:** 00_MASTER_PLAN.md

## 1. Mục tiêu (Objective)
*Mô tả ngắn gọn trong 1-2 câu. Ví dụ: Viết hàm `search_drug_smart` trong `services.py` sử dụng thuật toán Fuzzy.*

## 2. Phạm vi (Scope & Constraints) - QUAN TRỌNG
- **Files to edit:** `app/services.py`, `app/api/drugs.py`
- **Line limit:** < 200 lines.
- **Dependency:** Chỉ sử dụng `scikit-learn` và `SQLAlchemy`, không cài thêm thư viện mới.
- **Context:** Dữ liệu đầu vào là String tên thuốc, đầu ra là JSON object.

## 3. Input / Output Specification
- **Input:** ```json
  {"query": "Panadul Extra"}
```
- **Output:** ```json
  {"result": "Panadul Extra"}
``` 