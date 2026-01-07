# Domain: Diseases (ICD-10)

Quản lý danh mục bệnh lý dựa trên bảng mã tiêu chuẩn quốc tế ICD-10.

## 1. Bảng `diseases`
Bảng lưu trữ danh mục bệnh lý.

| Cột | Kiểu dữ liệu | Mô tả | Ghi chú |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | Khóa chính | |
| `icd_code` | TEXT | Mã ICD-10 (ví dụ: E11, I10) | |
| `disease_name` | TEXT | Tên bệnh chính thức | |
| `chapter_name` | TEXT | Tên chương (Chapter) trong ICD-10 | |
| `slug` | TEXT | Tên bệnh chuẩn hóa không dấu | |
| `search_text` | TEXT | Dữ liệu tìm kiếm tổng hợp | |
| `is_active` | TEXT | Trạng thái ('active'/'inactive') | |

## 2. Tìm kiếm (`diseases_fts`)
Hỗ trợ tìm kiếm nhanh theo:
- `icd_code`
- `disease_name`
- `search_text`
