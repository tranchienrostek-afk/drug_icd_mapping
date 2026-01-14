# 📝 PROJECT CHANGE REQUEST LOG (NHẬT KÝ THAY ĐỔI DỰ ÁN)

**Dự án:** AZINSU - Hệ thống Quản lý Dữ liệu & Nhận diện Thuốc
**Ngày khởi tạo:** 07/01/2026
**Trạng thái:** Active

---

## ⚠️ QUY TẮC VÀNG (GOLDEN RULES) - BẮT BUỘC ĐỌC

*Để đảm bảo tính toàn vẹn và khả năng truy vết (traceability), toàn bộ thành viên team phải tuân thủ tuyệt đối:*

1. **NGUYÊN TẮC "BẤT BIẾN" (IMMUTABILITY):** Tuyệt đối **KHÔNG ĐƯỢC XÓA hoặc SỬA** các log cũ phía trên. Mọi thay đổi đều phải viết tiếp xuống dưới cùng (Append-only).
2. **XỬ LÝ SAI SÓT:** Nếu một log trước đó bị sai hoặc cần hủy bỏ, hãy tạo một log mới bên dưới với nội dung *"Revert (Đảo ngược) thay đổi [Mã ID]..."* thay vì xóa dòng cũ.
3. **LÝ DO LÀ QUAN TRỌNG NHẤT:** Luôn ghi rõ mục *"Lý do/Rationale"*. Chúng ta cần biết *tại sao* thay đổi logic này để tránh lặp lại sai lầm trong tương lai.
4. **TRỌNG TÂM NGHIỆP VỤ:** Chỉ log những thay đổi về Logic, Cấu trúc DB, API, hoặc Quy trình nghiệp vụ. Các fix lỗi chính tả, format code nhỏ nhặt không cần ghi tại đây (hãy dùng Git Commit).
5. **FORMAT THỐNG NHẤT:** Sử dụng đúng Template mẫu ở cuối file khi thêm log mới.

---

## 📋 LỊCH SỬ THAY ĐỔI (LOGS)

### [CR-001] Khởi tạo dự án & Ban hành SRS

- **Thời gian:** 07/01/2026 08:30 AM
- **Người yêu cầu:** Trần Văn Chiến
- **Phân hệ:** Toàn hệ thống
- **Nội dung thay đổi:**
  - Thiết lập kiến trúc ban đầu.
  - Ban hành tài liệu SRS v1.0 và Sơ đồ kiến trúc hệ thống.
- **Lý do:** Bắt đầu giai đoạn triển khai (Deployment Phase).

---

### [CR-002] Cập nhật Logic Xử lý Trùng lặp Dữ liệu (Staging)

- **Thời gian:** 07/01/2026 10:15 AM
- **Người yêu cầu:** Trần Văn Chiến
- **Phân hệ:** Database / Data Entry
- **Nội dung thay đổi:**
  - **Logic CŨ:** Ghi đè ngay lập tức nếu trùng SĐK/Tên.
  - **Logic MỚI:** Chuyển vào trạng thái **Staging (Chờ xác nhận)**.
    - Hiển thị so sánh 2 bản ghi (Cũ vs Mới).
    - Cần API xác nhận để ghi đè.
    - Nếu ghi đè: Dữ liệu cũ chuyển vào Warehouse (Thùng rác/Lịch sử), Dữ liệu mới vào DB Chính.
- **Lý do:** Tuân thủ chính sách "No Delete Policy", đảm bảo dữ liệu cũ luôn được backup để truy vết.

---

### [CR-003] Mở rộng Schema Bảng Thuốc

- **Thời gian:** 07/01/2026 11:00 AM
- **Người yêu cầu:** Team Thẩm định
- **Phân hệ:** Database
- **Nội dung thay đổi:**
  - Thêm cột `classification` (Enum: Thuốc, Vitamin, TPCN, Thiết bị YT...).
  - Thêm cột `appraiser_note` (Text: Ghi chú của thẩm định viên).
- **Lý do:** - Phân loại rõ ràng các đối tượng không phải là thuốc.
  - Cung cấp ngữ cảnh (context) quan trọng để AI suy luận mối quan hệ Thuốc - Bệnh chính xác hơn.

---

### [CR-004] Chia nhỏ file code source

- **Thời gian:** 07/01/2026 13:10
- **Người yêu cầu:** Trần Văn Chiến
- **Phân hệ:** Design pattern
- **Nội dung thay đổi:**
  - Chia nhỏ file `web_crawler.py` thành `core_drug.py`, `main.py`, v.v. để đảm bảo quy tắc <200 dòng.
- **Lý do:** Tối ưu quá trình bảo trì và debug.

---

### [CR-005] Import DataCore & Schema Migration

- **Thời gian:** 09/01/2026 14:30
- **Người yêu cầu:** AI Architect
- **Phân hệ:** Database / Data Pipeline
- **Nội dung thay đổi:**
  - Nhập liệu 65,026 bản ghi thuốc từ DataCore.
  - Thêm cột `source_urls` vào bảng `drugs`.
  - Triển khai thuật toán "Smart Upsert" (In-memory Hash Map) để tăng tốc độ import.
- **Lý do:** Làm giàu dữ liệu nền tảng cho hệ thống.

---

### [CR-006] Nâng cấp Thuật toán Tìm kiếm (Hybrid Search v2.0)

- **Thời gian:** 09/01/2026 18:30
- **Người yêu cầu:** AI Scientist
- **Phân hệ:** Backend / Search Engine
- **Nội dung thay đổi:**
  - **Integration:** Tích hợp thư viện `rapidfuzz` để xử lý Fuzzy Search (bắt lỗi chính tả).
  - **Optimization:** Loại bỏ `so_dang_ky` khỏi Vector Index để giảm nhiễu Semantic Search.
  - **Tuning:** Hạ Threshold Vector Search xuống **0.75**.
- **Lý do:** Cải thiện Accuracy và Hit Rate khi tìm kiếm trên tập dữ liệu lớn (65k records).

---

### [CR-007] Tích hợp Browser MCP Agent vào Server (Task 027)

- **Thời gian:** 12/01/2026 13:00
- **Người yêu cầu:** Admin
- **Phân hệ:** Backend / Agent Service / Docker
- **Nội dung thay đổi:**
  - **Thêm mới:** Service `agent_search_service.py` (Class `BrowserAgentRunner`) để chạy Browser Agent headless.
  - **Thêm mới:** API Endpoint `POST /api/v1/drugs/agent-search` để kích hoạt tìm kiếm tự động qua AI Agent.
  - **Dockerfile:** Chuyển sang base image `mcr.microsoft.com/playwright/python:v1.40.0-jammy` để hỗ trợ Playwright.
  - **dependencies:** Thêm `mcp-agent`, `playwright` vào `requirements.txt`.
- **Lý do:** Bổ sung khả năng "Exhaustive Search" cho thuốc bằng AI Agent, bypass được các trang bị chặn Google.

---

### [CR-008] Triển khai Token Tracking Service (Task 028)

- **Thời gian:** 12/01/2026 13:30
- **Người yêu cầu:** Admin
- **Phân hệ:** Monitoring / Cost Management
- **Nội dung thay đổi:**
  - **Thêm mới:** Module `app/core/token_tracker.py` với class `TokenTracker`.
  - **Chức năng:** Ghi log mỗi lần gọi Azure OpenAI, bao gồm: Context, Model, Input/Output Tokens, Cost (USD).
  - **Output:** File JSON hàng ngày tại `logs/trace_token_openai/DD_MM_YYYY_total_tokens.json`.
  - **Tích hợp:** Hook vào `patched_request_completion_task` trong Agent Service.
- **Lý do:** Giám sát chi tiết chi phí OpenAI, tránh phát sinh ngoài kiểm soát.

---

### [CR-009] Triển khai API Logging Middleware (Task 029)

- **Thời gian:** 12/01/2026 13:30
- **Người yêu cầu:** Admin
- **Phân hệ:** Backend / Logging & Auditing
- **Nội dung thay đổi:**
  - **Thêm mới:** Module `app/middlewares/logging_middleware.py` với class `LogMiddleware`.
  - **Chức năng:** Chặn mọi request API, ghi lại Request Body, Response Body, Duration, Client IP.
  - **Output:** File log hàng ngày tại `logs/logs_api/DD_MM_YYYY_api.log`.
  - **Đăng ký:** Middleware được đăng ký trong `app/main.py`.
- **Lý do:** Tăng cường khả năng debug và audit toàn bộ luồng dữ liệu API.

---

## 📋 TEMPLATE CHO LOG MỚI (COPY & PASTE)

### [CR-XXX] Tiêu đề thay đổi ngắn gọn

- **Thời gian:** DD/MM/YYYY HH:MM
- **Người yêu cầu:** Tên người yêu cầu
- **Phân hệ:** API / DB / UI / Crawle
- **Nội dung thay đổi:**
  - Mô tả ngắn gọn hiện trạng cũ.
  - Mô tả chi tiết thay đổi mới.
- **Lý do:** Tại sao phải thay đổi? (Fix bug, thay đổi nghiệp vụ, tối ưu...)
