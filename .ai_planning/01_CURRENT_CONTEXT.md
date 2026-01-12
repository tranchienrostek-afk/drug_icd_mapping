# Context Hiện tại - Dự án AZINSU
<!-- Context hiện tại (AI đọc file này trước tiên) -->

## 1. Trạng thái hiện tại
- **Giai đoạn**: Giai đoạn 3: Tối ưu hoá & Mở rộng (Scaling Phase).
- **Tiến độ**: 
    - Đã hoàn tất nhập liệu **65,000 bản ghi thuốc** (DataCore) vào DB.
    - Đã nâng cấp thuật toán Search (Vector + Fuzzy) để xử lý dữ liệu lớn.
    - Đã thiết lập môi trường Git/GitHub và CI/CD cơ bản (Docker Rebuild).
- **Mục tiêu gần nhất**: Ổn định hóa hệ thống sau khi import lượng lớn dữ liệu và giám sát hiệu năng.

## 2. Thông tin Kỹ thuật Quan trọng (Architecture v2.0)
- **Cấu trúc Dữ liệu mới**:
    - Bảng `drugs` có thêm cột `source_urls` (Task 021/022).
    - `search_text` index đã được tối ưu (loại bỏ SDK, chuẩn hóa không dấu) phục vụ Vector Search.
- **Search Stack**:
    - **Backend**: `app/services.py` -> `DrugDbEngine` (Core Logic).
    - **Libs**: `rapidfuzz` (mới thêm), `sklearn` (TF-IDF), `playwright`.
    - **Vector Cache**: Load toàn bộ 65k thuốc vào RAM lúc khởi động (~100MB).
- **File System**: Đã dọn dẹp các script cũ vào thư mục `archive/` để giữ workspace gọn gàng.

## 3. Các vấn đề cần lưu ý (Critical Notes)
- **Rebuild Docker**: Do thêm thư viện mới (`rapidfuzz`, `playwrightdeps`), việc rebuild container mất nhiều thời gian (~15p).
- **RAM Usage**: Cần chú ý dung lượng RAM server do cơ chế load Cache Vector in-memory.
- **Search Threshold**: Vector Search Threshold hiện tại là **0.75**, Fuzzy Threshold là **85.0**.

## 4. Ưu tiên Công việc Tiếp theo
1.  **Monitor (Task 019)**: Theo dõi độ ổn định của API với 65k dữ liệu.
2.  **Web Crawler (Task 003)**: Duy trì như phương án dự phòng (Fallback).
3.  **Knowledge Graph (Task 023)**: Bắt đầu nghiên cứu liên kết thuốc với ICD-10 dựa trên dữ liệu `chi_dinh` phong phú vừa import.

---
*Tài liệu đã được cập nhật ngày 09/01/2026 sau sự kiện "DataCore Import".*