# ISSUE: BUG-000 - Lỗi kết nối Database SQLite
**Status:** Resolved
**Severity:** Critical
**Affected Component:** Database Service (`app/database/`)

## 1. Mô tả lỗi (Description)
Hệ thống không thể khởi chạy do không tìm thấy tệp tin `medical.db` hoặc đường dẫn tệp tin không chính xác khi chạy trong môi trường FastAPI.

## 2. Logs & Error Message (QUAN TRỌNG)
```text
sqlite3.OperationalError: unable to open database file
```

## 3. Cách khắc phục (Resolution)
- Chuyển đổi đường dẫn tương đối sang đường dẫn tuyệt đối hoặc định nghĩa môi trường `DATABASE_URL` trong tệp `.env`.
- Đảm bảo thư mục `app/database/` tồn tại trước khi khởi tạo kết nối.

## 4. Xác nhận (Verification)
Database đã kết nối thành công, có thể thực hiện truy vấn schema qua script `inspect_db_full.py`.
