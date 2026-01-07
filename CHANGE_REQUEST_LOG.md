# 📝 PROJECT CHANGE REQUEST LOG (NHẬT KÝ THAY ĐỔI DỰ ÁN)

**Dự án:** AZINSU - Hệ thống Quản lý Dữ liệu & Nhận diện Thuốc
**Ngày khởi tạo:** 07/01/2026
**Trạng thái:** Active

---

## ⚠️ QUY TẮC VÀNG (GOLDEN RULES) - BẮT BUỘC ĐỌC
*Để đảm bảo tính toàn vẹn và khả năng truy vết (traceability), toàn bộ thành viên team phải tuân thủ tuyệt đối:*

1.  **NGUYÊN TẮC "BẤT BIẾN" (IMMUTABILITY):** Tuyệt đối **KHÔNG ĐƯỢC XÓA hoặc SỬA** các log cũ phía trên. Mọi thay đổi đều phải viết tiếp xuống dưới cùng (Append-only).
2.  **XỬ LÝ SAI SÓT:** Nếu một log trước đó bị sai hoặc cần hủy bỏ, hãy tạo một log mới bên dưới với nội dung *"Revert (Đảo ngược) thay đổi [Mã ID]..."* thay vì xóa dòng cũ.
3.  **LÝ DO LÀ QUAN TRỌNG NHẤT:** Luôn ghi rõ mục *"Lý do/Rationale"*. Chúng ta cần biết *tại sao* thay đổi logic này để tránh lặp lại sai lầm trong tương lai.
4.  **TRỌNG TÂM NGHIỆP VỤ:** Chỉ log những thay đổi về Logic, Cấu trúc DB, API, hoặc Quy trình nghiệp vụ. Các fix lỗi chính tả, format code nhỏ nhặt không cần ghi tại đây (hãy dùng Git Commit).
5.  **FORMAT THỐNG NHẤT:** Sử dụng đúng Template mẫu ở cuối file khi thêm log mới.

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

### [CR-XXX] Tiêu đề thay đổi ngắn gọn
- **Thời gian:** DD/MM/YYYY HH:MM
- **Người yêu cầu:** Tên người yêu cầu
- **Phân hệ:** API / DB / UI / Crawler...
- **Nội dung thay đổi:**
  - Mô tả ngắn gọn hiện trạng cũ.
  - Mô tả chi tiết thay đổi mới.
- **Lý do:** Tại sao phải thay đổi? (Fix bug, thay đổi nghiệp vụ, tối ưu...)