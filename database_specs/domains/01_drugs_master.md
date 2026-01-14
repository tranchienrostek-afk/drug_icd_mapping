# Domain: Drugs Master

Dữ liệu chủ đề (Master Data) về thuốc, bao gồm thông tin hành chính, thành phần và chỉ định.

## 1. Bảng `drugs`
Bảng lưu trữ dữ liệu thuốc chính thức sau khi đã qua kiểm duyệt.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng (RowID) |
| `ten_thuoc` | TEXT | Tên thương mại của thuốc |
| `so_dang_ky` | TEXT | Số đăng ký lưu hành (SDK) |
| `hoat_chat` | TEXT | Tên hoạt chất chính |
| `cong_ty_san_xuat` | TEXT | Công ty sản xuất |
| `chi_dinh` | TEXT | Công dụng và chỉ định điều trị |
| `tu_dong_nghia` | TEXT | Từ đồng nghĩa (hỗ trợ search) |
| `classification` | TEXT | Phân loại bổ sung (ETC/OTC/...) |
| `note` | TEXT | Ghi chú từ thẩm định viên |
| `is_verified` | INTEGER | Trạng thái xác minh (1=Verified) |
| `search_text` | TEXT | Trường tổng hợp cho FTS Search |
| `created_by` | TEXT | Người tạo |
| `created_at` | TIMESTAMP | Thời điểm tạo |
| `updated_by` | TEXT | Người cập nhật cuối cùng |
| `updated_at` | TIMESTAMP | Thời điểm cập nhật cuối |

## 2. Bảng `drug_staging`
Khu vực trung gian (Staging Area) lưu trữ dữ liệu thô từ Crawler, Import hoặc đóng góp từ cộng đồng trước khi được duyệt vào bảng chính.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng |
| `ten_thuoc` | TEXT | Tên thuốc đề xuất |
| `so_dang_ky` | TEXT | SDK đề xuất |
| `hoat_chat` | TEXT | Hoạt chất |
| `cong_ty_san_xuat` | TEXT | Công ty SX |
| `chi_dinh` | TEXT | Chỉ định |
| `tu_dong_nghia` | TEXT | Từ đồng nghĩa |
| `search_text` | TEXT | Text tìm kiếm thô |
| `status` | TEXT | Trạng thái: `pending`, `approved`, `rejected` |
| `conflict_type` | TEXT | Loại xung đột phát hiện: `sdk` (trùng SDK), `name` (trùng tên) |
| `conflict_id` | INTEGER | ID của thuốc gốc trong bảng drugs (nếu conflict) |
| `classification` | TEXT | Phân loại |
| `note` | TEXT | Ghi chú |
| `created_by` | TEXT | Người submit |
| `created_at` | TIMESTAMP | Thời điểm submit |

## 3. Tìm kiếm (`drugs_fts`)
Bảng ảo (Virtual Table) sử dụng FTS5 để hỗ trợ tìm kiếm toàn văn tốc độ cao.
- **Cột index**: `ten_thuoc`, `hoat_chat`, `cong_ty_san_xuat`, `search_text`.
- **Cơ chế**: Dùng tokenizer để tách từ, hỗ trợ prefix search (`query*`).
