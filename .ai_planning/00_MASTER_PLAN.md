# AZINSU - Hệ thống Quản lý Dữ liệu & Nhận diện Thuốc
<!-- Bản đồ tổng thể, roadmap dự án -->

## I. Tổng quan Dự án
Hệ thống quản lý dữ liệu thuốc và liên kết bệnh lý (ICD-10), bao gồm các tính năng tự động tìm kiếm (Web Crawler), xử lý dữ liệu thông minh và phân tích điều trị bằng AI.

## II. Roadmap & Trạng thái (Status Tracker)

### Giai đoạn 1: Xây dựng Nền tảng (Completed ✅)
- [x] Thiết lập Database SQLite (`medical.db`)
- [x] API nhận diện thuốc cơ bản
- [x] Web Crawler (Playwright)

### Giai đoạn 2: Bùng nổ Dữ liệu (Completed ✅)
- [x] **Import DataCore:** Tiếp nhận và xử lý 65,026 bản ghi thuốc sạch vào Database (Task 022).
- [x] **Smart Upsert:** Cơ chế update thông minh, tránh trùng lặp dữ liệu lớn (Task 021).
- [x] **Schema Migration:** Tự động mở rộng cấu trúc dữ liệu (`source_urls`).

### Giai đoạn 3: Nâng cấp Trí tuệ (In Progress 🚀)
- [x] **Algorithm Upgrade:** Tối ưu hóa Vector Search (loại bỏ nhiễu SDK) & Tích hợp RapidFuzz (Task 018).
- [ ] **Performance Monitor:** Theo dõi RAM usage khi Data tăng trưởng.
- [ ] **Knowledge Graph:** Xây dựng liên kết Thuốc - Bệnh (ICD-10).

## III. Danh sách Task (.ai_planning)

### Mới Hoàn thành (Recently Completed)
1.  `task_022_import_datacore.md`: Import 65k dữ liệu Kho báu (DataCore).
2.  `task_021_import_and_deduplicate.md`: Xây dựng module Smart Upsert & Data Refinery.
3.  `task_018_optimize_search_algorithm.md`: Nâng cấp thuật toán tìm kiếm (Fuzzy/Vector).
4.  `task_020_data_refinery_logic.md`: Chuẩn hóa dữ liệu thô.

### Đang thực hiện (Active)
1.  `task_023_knowledge_graph.md` (Planned): Liên kết dữ liệu thuốc với ICD.
2.  `task_019_monitor_performance.md` (Planned): Giám sát hệ thống.

## IV. Tài liệu Tham khảo
- [Báo cáo Giải pháp 09/01/2026](file:///C:/Users/Admin/Desktop/drug_icd_mapping/.ai_planning/.implementation_rules/.ai_reports/2026-01/drug_solution_report_20260109.md)
- [Tech Blueprint](file:///C:/Users/Admin/Desktop/drug_icd_mapping/.memory/03_tech_blueprint.md)