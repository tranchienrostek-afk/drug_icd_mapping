# Domain: System Admin & History

Các bảng phục vụ quản trị hệ thống, truy vết dữ liệu (Audit Trail) và quản lý thay đổi.

## 1. Truy vết Thuốc (`drug_history`)
Lưu trữ phiên bản cũ của thuốc khi có sự thay đổi thông tin trong bảng `drugs`.
- `original_drug_id`: Liên kết về ID thuốc gốc.
- `archived_at`: Thời điểm lưu trữ.

## 2. Truy vết Staging (`drug_staging_history`)
Lưu trữ lịch sử xử lý các bản ghi staging (Approved, Rejected, Cleared).
- `original_staging_id`: ID gốc từ bảng `drug_staging`.
- `action`: Hành động đã thực hiện (xem `enum_definitions.md`).

## 3. Quản lý chung
- `sqlite_sequence`: Bảng hệ thống của SQLite để quản lý các trường AUTOINCREMENT.
- `created_by`, `updated_by`: Truy vết người thực hiện thay đổi trên các bản ghi.
