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

> - Alias khi SELECT: `disease_icd as icd_code`, `disease_name_norm as disease_name`

## 3. Nguồn Dữ Liệu (Source Data) - `icd_data.csv`
Thư mục: `C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\to_database\icd_data.csv`

Dataset chứa danh mục bệnh ICD-10 đầy đủ.
- **Kích thước**: ~4.7 MB
- **Số lượng bản ghi**: ~15,800+ dòng

### Cấu trúc dự kiến (CSV Header mapping)
Dựa trên dữ liệu mẫu, file CSV không có header rõ ràng ở dòng 1 (hoặc dòng 1 là data). Cần kiểm tra kỹ dòng đầu tiên khi import.
Tuy nhiên, cấu trúc các cột quan trọng nhận diện được:
- `id` (UUID): Cột 1 (ví dụ: `834d33eb...`)
- `icd_code` (Mã bệnh): Cột 10 (ví dụ: `G23.3`, `C84.8`)
- `disease_name` (Tên bệnh): Cột 14 (ví dụ: `Teo đa hệ thống thể tiểu não [MSA- C]`)
- `disease_name_unsigned` (Tên không dấu): Cột 13 (ví dụ: `teoahethongthetieunao...`)
- `chapter_name` (Tên chương): Cột 12 (ví dụ: `Hội chứng ngoại tháp và rối loạn vận động`)

**Action Item:** Cần viết script import ánh xạ đúng index cột (CSV không header).
