# Domain: Drugs Master

Dữ liệu chủ đề (Master Data) về thuốc, bao gồm thông tin hành chính, thành phần và chỉ định.

## 1. Bảng `drugs`
Bảng lưu trữ dữ liệu thuốc chính thức sau khi đã qua kiểm duyệt.

| Cột | Kiểu dữ liệu | Mô tả | Ghi chú |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | Khóa chính (UUID hoặc định danh duy nhất) | |
| `ten_thuoc` | TEXT | Tên thương mại của thuốc | |
| `so_dang_ky` | TEXT | Số đăng ký lưu hành (SDK) | |
| `hoat_chat` | TEXT | Tên hoạt chất chính | |
| `ham_luong_thuoc`| TEXT | Hàm lượng hoạt chất | |
| `chi_dinh` | TEXT | Công dụng và chỉ định điều trị | |
| `nhom_duoc_ly` | TEXT | Nhóm dược lý của thuốc | |
| `classification` | TEXT | Phân loại bổ sung (AI/Expert) | Trường mới (Task 004) |
| `note` | TEXT | Ghi chú từ thẩm định viên | Trường mới (Task 004) |
| `is_verified` | INTEGER | Trạng thái xác minh (0 hoặc 1) | |

## 2. Bảng `drug_staging`
Thư mục đệm lưu trữ dữ liệu thô từ crawler hoặc import trước khi merge vào bảng chính.

- `conflict_type`: Xác định lý do trùng lặp (`sdk` hoặc `name`).
- `status`: Mặc định là `pending`.

## 3. Tìm kiếm (`drugs_fts`)
Bảng ảo hỗ trợ tìm kiếm toàn văn trên các trường: `ten_thuoc`, `hoat_chat`, `search_text`.
