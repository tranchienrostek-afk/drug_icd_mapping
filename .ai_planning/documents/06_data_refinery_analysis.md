# Phân Tích `app/data_refinery.py`

Module `data_refinery.py` đóng vai trò là bộ lọc và xử lý dữ liệu thô (ETL Helper) trước khi đưa vào cơ sở dữ liệu. Class `DataRefinery` chịu trách nhiệm chuẩn hóa, làm sạch và loại bỏ trùng lặp.

## 1. Mục Đích Chính

Xử lý các file CSV/Excel đầu vào (thường từ nguồn crawler hoặc import thủ công) để đảm bảo chất lượng dữ liệu cao nhất có thể.

## 2. Các Chức Năng Cốt Lõi

### a. `load_csv(file_path)`
- Tải file CSV một cách an toàn.
- Xử lý lỗi thường gặp như `on_bad_lines='skip'` (bỏ qua các dòng lỗi định dạng).
- Ghi log số lượng dòng tải được.

### b. `clean_and_deduplicate(df)`
Đây là trái tim của quy trình làm sạch dữ liệu.

1.  **Chuẩn hóa String**: Loại bỏ khoảng trắng thừa ở đầu/cuối của tên cột và giá trị dữ liệu (trim/strip).
2.  **Smart Deduplication (Khử trùng lặp thông minh)**:
    - Thay vì chỉ giữ dòng đầu tiên hoặc cuối cùng một cách ngẫu nhiên, thuật toán sẽ tính **Core Score (Độ hoàn thiện)** cho từng dòng.
    - `completeness_score`: Tổng số trường có dữ liệu (không null, không rỗng).
    - Dữ liệu được sắp xếp theo `so_dang_ky` và `completeness_score` (giảm dần).
    - -> **Kết quả**: Với cùng một Số Đăng Ký, hệ thống sẽ giữ lại bản ghi có nhiều thông tin chi tiết nhất.

### c. `extract_info_from_description(text)`
- Một hàm heuristic đơn giản để trích xuất thông tin từ các trường văn bản không có cấu trúc.
- Hiện tại mappping `noi_dung_dieu_tri` sang `chi_dinh`. Có thể mở rộng để dùng Regex tách `chong_chi_dinh` nếu cấu trúc văn bản rõ ràng hơn.

### d. `process_for_import(df)`
- Chuyển đổi dữ liệu từ Pandas DataFrame sang danh sách Dictionary chuẩn để lưu vào Database.
- Thực hiện mapping tên cột từ CSV sang tên cột DB:
    - `ham_luong` -> `nong_do`
    - `danh_muc` -> `nhom_thuoc`
    - `url_nguon` -> `source_urls`
- Làm sạch các giá trị `nan` (Not a Number) của Pandas thành `None` hoặc loại bỏ để tránh lỗi dữ liệu bẩn khi insert.

## Quy Trình Tóm Tắt

```mermaid
graph LR
    Input[File CSV Thô] --> Load[Load & Skip Bad Lines]
    Load --> Clean[Strip Whitespace]
    Clean --> Score[Tính Độ Hoàn Thiện]
    Score --> Dedup[Giữ Bản Ghi Tốt Nhất]
    Dedup --> Map[Map sang DB Schema]
    Map --> Output[List Dict (Ready for DB)]
```
