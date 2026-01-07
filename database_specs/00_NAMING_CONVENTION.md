# Quy tắc đặt tên (Naming Convention)

Tài liệu này quy chuẩn cách đặt tên trong cơ sở dữ liệu `medical.db`.

## 1. Tables
- Tên bảng: Sử dụng `snake_case` và số nhiều (plural).
- Ví dụ: `drugs`, `diseases`, `drug_disease_links`.
- Bảng phụ/staging: Hậu tố `_staging`, `_history`, `_fts`.

## 2. Columns
- Tên cột: Sử dụng `snake_case`.
- Ví dụ: `ten_thuoc`, `so_dang_ky`, `created_at`.
- Khóa chính (Primary Key): Thường là `id`.
- Khóa ngoại (Foreign Key): Định dạng `table_singular_id` hoặc `ref_id_...`.
  - Ví dụ: `drug_id`, `disease_id`, `ref_id_nhom`.

## 3. Data Types & Formats
- **Boolean**: Sử dụng `INTEGER` (0: False/No, 1: True/Yes) hoặc `TEXT` ('active', 'inactive').
- **Timestamps**: Định dạng `TEXT` (ISO 8601) hoặc `TIMESTAMP` (`CURRENT_TIMESTAMP`).
- **ICD Codes**: Tên cột `icd_code`, giá trị in hoa (ví dụ: `E11`).

## 4. Full-Text Search (FTS)
- Sử dụng hậu tố `_fts` cho các bảng ảo FTS5.
- Cột tìm kiếm tổng hợp: `search_text`.
