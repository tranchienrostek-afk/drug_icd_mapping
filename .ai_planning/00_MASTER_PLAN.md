# AZINSU - Hệ thống Quản lý Dữ liệu & Nhận diện Thuốc
<!-- Bản đồ tổng thể, roadmap dự án -->

## I. Tổng quan Dự án
Hệ thống quản lý dữ liệu thuốc và liên kết bệnh lý (ICD-10), bao gồm các tính năng tự động tìm kiếm (Web Crawler), xử lý dữ liệu thông minh và phân tích điều trị bằng AI.

## II. Roadmap & Trạng thái (Status Tracker)

### Giai đoạn 1: Xây dựng Nền tảng (Completed)
- [x] Thiết lập Database SQLite (`medical.db`)
- [x] API nhận diện thuốc (Identity API - Tầng Database)
- [x] Web Crawler cơ bản (Tìm kiếm thông tin thuốc từ các nguồn DAV, TBD)

### Giai đoạn 2: Nâng cấp & Kiểm thử (Completed)
- [x] **Task 004**: Kiểm thử API Phân tích điều trị (Treatment Analysis)
- [x] **Task 005**: Rà soát PRD (Requirements) & Validate Schema dữ liệu
- [x] **Task 006**: Thiết lập Git, GitHub cho dự án

### Giai đoạn 3: Tối ưu hóa & Mở rộng (In Progress)
- [ ] Tối ưu hóa Web Crawler (Stop Early, Dynamic Selectors)
- [ ] Hoàn thiện Dashboard Admin cho Staging Data
- [ ] Mở rộng Knowledge Graph liên kết Thuốc - Triệu chứng

## III. Danh sách Task (.ai_planning)

### Hoàn thành (Completed)
1. `task_004_api_testing_bugfix.md`: Sửa lỗi trích xuất ICD và Deduplication.
2. `task_005_prd_review_validation.md`: Rà soát yêu cầu kỹ thuật.
3. `task_006_git_github_setup.md`: Quản lý phiên bản.

### Đang thực hiện (Active)
1. `task_001_setup_db.md`: Quản lý cấu trúc dữ liệu.
2. `task_002_api_identify.md`: Tối ưu hóa API nhận diện.
3. `task_003_web_crawler_basic.md`: Nâng cấp scraper.

## IV. Tài liệu Tham khảo
- [Requirements Document](file:///c:/Users/Admin/Desktop/drug_icd_mapping/requirements_document.txt)
- [Walkthrough Documentation](file:///C:/Users/Admin/.gemini/antigravity/brain/e39346ff-4b82-4a84-bec9-634d2c7b18fd/walkthrough.md)