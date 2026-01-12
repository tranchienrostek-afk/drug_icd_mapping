# TASK TICKET: [TASK_022] - [Import Full DataCore ThuocBietDuoc]

**Status:** Done
**Priority:** Critical
**Người Tạo:** AI Agent
**Ngày tạo:** 09.01.2026
**Ngày hoàn thành:** 09.01.2026

**Linked to:** `task_021_import_and_deduplicate_drug_data.md`

---

## 6. Implementation Results

- **Data Processing**:
    - **Source**: 8 CSV files from `datacore_thuocbietduoc`.
    - **Total Raw Rows**: 83,770 lines.
    - **Cleaned & Deduplicated**: 64,930 unique records.
- **Database Import**:
    - **Strategy**: In-memory Cache Checking (Optimization) + Partial Update.
    - **Execution Time**: Fast (~1-2 minutes).
    - **Results**:
        - **Inserted New**: 62,406 drugs.
        - **Updated**: 89 drugs.
        - **Total DB Count**: ~65,026 drugs.
- **Verification**:
    - Confirmed data integrity via `check_db_import.py`.

---

## 1. Mục tiêu (Objective)

Người dùng đã cung cấp "Kho báu" dữ liệu tại `knowledge for agent/datacore_thuocbietduoc`. Đây là tập hợp dữ liệu crawl toàn diện (full crawl).
Mục tiêu là **hợp nhất tất cả các file CSV** trong thư mục này, xử lý làm sạch, khử trùng lặp và nhập toàn bộ vào `medical_knowledge.db`.

---

## 2. Phân tích Nguồn Dữ liệu

Vị trí: `C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\datacore_thuocbietduoc`
Các file chính:
- `ketqua_thuoc_part_20260108_104310.csv` (~20MB)
- `ketqua_thuoc_part_20260106_190030.csv` (~17MB)
- Và các file nhỏ khác.

Tổng dung lượng ~40MB CSV. Ước tính số lượng bản ghi raw: 30,000 - 50,000 dòng.
Sau khi deduplicate (theo SDK), dự kiến còn khoảng 20,000 - 30,000 đầu thuốc unique.

---

## 3. Implementation Plan

### Step 1: Data Consolidation
- Script đọc tất cả file `.csv` trong folder target.
- Merge vào một Pandas DataFrame duy nhất.
- Áp dụng logic `clean_and_deduplicate` của `DataRefinery`.

### Step 2: Database Import Strategy
- Sử dụng chiến lược **Smart Upsert** đã kiểm chứng ở Task 21.
- Tối ưu hóa performance: Sử dụng `executemany` cho batch update/insert (nếu cần thiết, do số lượng lớn hơn).

### Step 3: Validation & Backup
- **Backup DB** trước khi chạy (`medical_knowledge.db` -> `medical_knowledge.bak`).
- Verify tổng số thuốc sau khi import.

---

## 4. Acceptance Criteria

| # | Criteria | Validated By |
|---|----------|--------------|
| 1 | Đọc và merge thành công tất cả file CSV trong DataCore. | Log output (Total raw rows). |
| 2 | Khử trùng lặp hiệu quả (giữ lại bản ghi tốt nhất). | Log output (Unique rows). |
| 3 | Import thành công vào DB mà không gây lỗi schema/data. | DB Query count. |
| 4 | Tổng số thuốc trong DB phản ánh đúng quy mô dữ liệu (dự kiến > 10,000). | `SELECT count(*) FROM drugs`. |

---

## 5. Execution Script Reference
- Script: `scripts/run_import_datacore.py` (New)
- Lib: `app/data_refinery.py` (Reuse)
