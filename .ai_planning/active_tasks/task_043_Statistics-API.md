# Task 043: Hệ Thống Thống Kê API Chi Tiết

## 🎯 Mục tiêu
Triển khai hệ thống thống kê chi tiết cho hai API chính (`/mapping/match` và `/consult_integrated`) với khả năng lọc theo thời gian và hiển thị kết quả chi tiết từng request.

---

## 🛠️ Backend (Monitor Service)
- [x] Cập nhật schema `monitor.db` (nếu cần) để lưu trữ đầy đủ payload request/response.
- [x] Triển khai logic tính toán thống kê theo thời gian (Ngày, Tuần, Tháng).
- [x] API `/api/v1/admin/request_logs`:
    - [x] Hỗ trợ filter theo `endpoint` và `date_range`.
    - [x] Trả về thống kê tổng hợp: Total, Success, Failure, %, Coverage (đối với consult).
- [x] Log chi tiết cho `/mapping/match` và `/mapping/match_v2`:
    - [x] Lưu cặp thuốc đã khớp (claim vs medicine).
    - [x] Lưu các thuốc không khớp (anomalies).
- [x] Log chi tiết cho `/consult_integrated`:
    - [x] Lưu trạng thái `validity`, `category`, và `role` của từng thuốc trong response.

---

## 💻 Frontend (Dashboard & Tab System Status)

### 📊 Thống Kê Tổng Quan (API Cards & Filters)
- [x] Thêm bộ lọc thời gian (Hôm nay, Tuần này, Tháng này).
- [x] `/api/v1/mapping/match` (incl. v2) card:
    - [x] Tổng request, Thành công/Thất bại, Tỷ lệ %.
- [x] `/api/v1/consult_integrated` card:
    - [x] Tổng request, Thành công/Thất bại, Tỷ lệ %.
    - [x] Tỷ lệ bao phủ (Coverage): Thuốc có role / Tổng số thuốc truyền vào.

### 📋 Bảng Danh Sách Request
- [x] Hiển thị danh sách request theo thời gian thực (hoặc refresh).
- [x] Phân loại theo Endpoint (Tabs hoặc lọc).
- [x] Cột: Thời gian, ID, Endpoint, Status, Latency, Found/NotFound.

### 🔍 Modal Chi Tiết Request (Cải thiện cực kỳ chi tiết)
- [x] Hiển thị thông tin base: ID, Status, Latency.
- [x] **Đối với `/mapping/match` (và v2):**
    - [x] Bảng các thuốc khớp thành công: Claim Service | Medicine Service | Confidence Score | Match Status.
    - [x] Bảng các thuốc không khớp (Anomalies): Claim Service | Lý do (Reason). (Nổi bật màu đỏ/cam).
- [x] **Đối với `/consult_integrated`:**
    - [x] Bảng chi tiết toàn bộ thuốc truyền vào:
        - Tên thuốc | SDK | Category | Validity | Role.
        - Dùng màu sắc: [Xanh] cho thuốc tìm thấy (có Role/Valid), [Đỏ] cho thuốc không tìm thấy.
    - [x] Hiển thị riêng phần Feedback gợi ý (nếu có).

---

## ✅ Kiểm Thử & Xác Minh
- [x] Kiểm tra tính chính xác của tỷ lệ % thành công/thất bại. (Verified via `verify_stats_calculation.py`)
- [x] Kiểm tra tính chính xác của tỷ lệ bao phủ (Knowledge Base Coverage). (Verified: Normalized ICD Match fixed)
- [x] Kiểm tra các bộ lọc Ngày/Tuần/Tháng hoạt động đúng với dữ liệu trong DB.
- [x] Xác minh giao diện Modal hiển thị đầy đủ và tường minh kết quả từ API response.
