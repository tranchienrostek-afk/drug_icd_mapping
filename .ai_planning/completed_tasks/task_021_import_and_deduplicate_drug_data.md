# TASK TICKET: [TASK_021] - [Import & Khử trùng lặp Dữ liệu Thuốc Biệt Dược]

**Status:** Done
**Priority:** High
**Người Tạo:** AI Agent
**Ngày tạo:** 09.01.2026
**Ngày hoàn thành:** 09.01.2026

**Linked to:** `task_020_integrate_solution_v03.md` (Reference Style)

---

## 6. Implementation Results

- **Data Analysis**: 
    - Source: `ketqua_thuoc_part_20260107_154800.csv` (2594 rows).
    - Duplicates found: ~14 (SDK based).
    - Cleaned unique records: 2580.
- **Database Import**:
    - Created `app/data_refinery.py` for cleaning & deduplication.
    - Created `scripts/run_import_task_021.py` for smart upsert.
    - **Outcome**: 2580 records processed.
        - Initial run: Inserted all.
        - Re-run (test): Updated all (added `source_urls`).
    - **Schema Change**: Added `source_urls` column to `drugs` table.
- **Verification**:
    - Verified `source_urls` population.
    - Verified no duplicate SDKs introduced.

---

## 1. Mục tiêu (Objective)

Người dùng đã thu thập được một bộ dữ liệu "siêu đẳng cấp" từ trang Thuốc Biệt Dược (~8000 rows), chứa thông tin chi tiết về thuốc.
Mục tiêu là **xử lý, làm sạch và nhập** bộ dữ liệu này vào `medical_knowledge.db` một cách thông minh, đảm bảo:
- **Không trùng lặp** (Deduplication).
- **Khai thác tối đa thông tin** (Full Extraction), không bỏ sót trường nào.
- **Chuẩn hóa** dữ liệu đầu vào.

---

## 2. Phân tích Dữ liệu (Analysis)

### 2.1 Cấu trúc Dữ liệu nguồn (`ketqua_thuoc_part_20260107_154800.csv`)

| Header CSV | Target Table Column (`drugs`) | Ghi chú |
|------------|-------------------------------|---------|
| `so_dang_ky` | `so_dang_ky` (Unique Key 1) | Cần chuẩn hóa, loại bỏ khoảng trắng thừa. |
| `ten_thuoc` | `ten_thuoc` | Tên thương mại. |
| `hoat_chat` | `hoat_chat` | Thành phần hoạt chất. |
| `noi_dung_dieu_tri` | `chi_dinh` (Main), `chong_chi_dinh`, `lieu_dung` | *Complex Logic*: Trường này chứa văn bản dài, có thể chứa cả chỉ định, liều dùng... Cần heuristic để tách hoặc gộp vào `chi_dinh` và `mo_ta`. |
| `dang_bao_che` | `bao_che` | Dạng bào chế. |
| `danh_muc` | `nhom_thuoc` | Phân loại/Danh mục. |
| `ham_luong` | `nong_do` | Hàm lượng/Nồng độ. |
| `url_nguon` | `source_urls` | Nguồn dữ liệu. |

### 2.2 Vấn đề Trùng lặp & Giải pháp

- **Vấn đề:** Nhiều dòng dữ liệu có cùng SĐK hoặc Tên thuốc + Hoạt chất giống nhau (do crawl nhiều lần hoặc phân trang).
- **Logic Khử trùng (Deduplication Rules):**
    1. **Primary Key Dedupe:** Dùng `so_dang_ky` làm khóa chính.
    2. **Conflict Resolution:** Nếu gặp trùng `so_dang_ky`:
        - Giữ lại bản ghi có **số lượng trường thông tin KHÁC null nhiều hơn**.
        - Nếu tương đương, giữ lại bản ghi có **độ dài text (`noi_dung_dieu_tri`) dài hơn**.
    3. **No-SDK Handling:** Nếu không có SĐK, check trùng theo `ten_thuoc` (normalize) + `hoat_chat` (normalize).

---

## 3. Implementation Plan

### Phase 1: Data Refinery Script (`app/data_refinery.py`)

Tạo module chuyên biệt để xử lý dữ liệu thô:
- `load_csv()`: Đọc CSV an toàn (handle multiline chars).
- `clean_record()`: Chuẩn hóa text, strip whitespace.
- `deduplicate_records()`: Áp dụng logic khử trùng nêu trên.
- `extract_fields()`: Heuristic parser cho trường `noi_dung_dieu_tri`.

### Phase 2: Database Keeper (`app/services.py` update)

Cập nhật `DrugDbEngine` để hỗ trợ **Batch Import** an toàn:
- `file_import_staging_drugs()`: Import vào bảng tạm hoặc xử lý upsert trực tiếp.
- Do user yêu cầu "chạy rules cho vào database", ta sẽ thực hiện chiến lược **Smart Upsert**:
    - Check tồn tại trong DB.
    - Nếu chưa -> Insert.
    - Nếu có -> Update các trường còn thiếu (Missing Information Fill).
    - Log lại các thay đổi.

### Phase 3: Execution & Report

- Tạo script chạy import: `scripts/run_import_task_021.py`.
- Xuất report sau khi chạy:
    - Total Rows Read.
    - Duplicates Removed.
    - New Records Inserted.
    - Existing Records Updated.

---

## 4. Acceptance Criteria

| # | Criteria | Validated By |
|---|----------|--------------|
| 1 | Đọc thành công file CSV 1.6MB (~8000 dòng). | Script log. |
| 2 | Loại bỏ hoàn toàn các dòng trùng lặp SDK. | Count distinct SDK vs Total rows. |
| 3 | Dữ liệu trường dài (`noi_dung_dieu_tri`) không bị cắt cụt. | Random spot check. |
| 4 | Dữ liệu được lưu vào Database (`medical_knowledge.db`). | SQLite query check. |
| 5 | Các trường thông tin bổ sung (`dang_bao_che`, `ham_luong`) được map đúng. | DB Inspection. |

---

## 5. References

- Data Source: `ketqua_thuoc_part_20260107_154800.csv`
- Previous Task: `task_020_integrate_solution_v03.md` (Multi-engine search)
