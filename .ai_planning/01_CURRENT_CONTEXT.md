# Context Hiện tại - Dự án AZINSU
<!-- Context hiện tại (AI đọc file này trước tiên) -->

## 1. Trạng thái hiện tại
- **Giai đoạn**: Giai đoạn 3: Tối ưu hóa & Mở rộng.
- **Tiến độ**: Đã hoàn thành kiểm thử API lõi, rà soát yêu cầu kỹ thuật (PRD) và thiết lập môi trường Git/GitHub.
- **Mục tiêu gần nhất**: Tối ưu hóa hiệu suất Web Crawler và hoàn thiện luồng dữ liệu Staging.

## 2. Thông tin Kỹ thuật Quan trọng
- **Cấu trúc Thư mục**:
    - `fastapi-medical-app/`: Mã nguồn chính của ứng dụng FastAPI.
    - `app/database/medical.db`: Cơ sở dữ liệu SQLite chính.
    - `app/service/web_crawler.py`: Logic cào dữ liệu thuốc/bệnh (Playwright).
- **Trường dữ liệu mới**: Đã cập nhật bảng `drugs` với các trường `classification` và `note` phục vụ suy luận AI.
- **Git Repository**: [tranchienrostek-afk/drug_icd_mapping](https://github.com/tranchienrostek-afk/drug_icd_mapping.git)

## 3. Các vấn đề cần lưu ý (Critical Notes)
- **Web Crawler**: Selector thường xuyên thay đổi, mã nguồn hiện tại đang sử dụng bộ chọn mới nhất (đã tối ưu hóa hơn so với PRD).
- **Deduplication**: Logic gộp thuốc đã được sửa lỗi cho trường hợp thuốc không có số đăng ký (SDK).
- **Inference**: AI sử dụng dữ liệu từ trường `note` (thẩm định viên) làm căn cứ ưu tiên khi không tìm thấy liên kết cứng trong DB.

## 4. Ưu tiên Công việc Tiếp theo
1. **Task 003 (Active)**: Cải thiện Web Crawler (Cơ chế Stop Early khi tìm đủ kết quả).
2. **Task 002 (Active)**: Tối ưu hóa API Identify để giảm độ trễ (Latency).
3. **Data Refinery**: Làm sạch dữ liệu rác trong bảng `drug_staging`.

---
*Tài liệu này được cập nhật tự động sau mỗi phiên làm việc để đảm bảo AI nắm bắt được context mới nhất.*