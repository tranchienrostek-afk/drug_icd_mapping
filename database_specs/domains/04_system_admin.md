# Domain: System Admin & Audit Logs

Quản lý dữ liệu hệ thống, nhật ký truy vết (Audit Trail) và dữ liệu thô đầu vào (Raw Logs).

## 1. Nhật ký Thay đổi Thuốc (`drug_history`)
Lưu trữ bản sao (Snapshot) của thuốc trước khi bị chỉnh sửa hoặc ghi đè.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính |
| `original_drug_id` | INTEGER | ID của thuốc gốc trong bảng `drugs` |
| `ten_thuoc` | TEXT | Tên thuốc cũ |
| `hoat_chat` | TEXT | Hoạt chất cũ |
| `cong_ty_san_xuat` | TEXT | Công ty cũ |
| `so_dang_ky` | TEXT | SDK cũ |
| `chi_dinh` | TEXT | Chỉ định cũ |
| `archived_at` | TIMESTAMP | Thời điểm lưu trữ |
| `archived_by` | TEXT | Người thực hiện thay đổi |

## 2. Nhật ký Staging (`drug_staging_history`)
Lưu trữ lịch sử các bản ghi Staging đã được xử lý (Approved/Rejected/Cleared).

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính |
| `original_staging_id`| INTEGER | ID gốc trong bảng `drug_staging` |
| `ten_thuoc` | TEXT | Tên thuốc |
| `so_dang_ky` | TEXT | SDK |
| `action` | TEXT | Hành động: `approved`, `rejected`, `cleared` |
| `archived_at` | TIMESTAMP | Thời điểm xử lý |
| `archived_by` | TEXT | Người xử lý |

## 3. Nhật ký Dữ liệu Thô (`raw_logs`)
Lưu trữ dữ liệu gốc từ quá trình ETL/Data Ingestion để đối chiếu khi cần thiết.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính |
| `batch_id` | TEXT | Mã lô import (UUID) |
| `raw_content` | TEXT | Nội dung thô (JSON/CSV row) |
| `source_ip` | TEXT | IP nguồn đẩy dữ liệu |
| `created_at` | TIMESTAMP | Thời điểm nhận |
