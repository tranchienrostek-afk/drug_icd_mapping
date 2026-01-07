<!-- Quy tắc nghiệp vụ cứng (Ví dụ: No Delete Policy) -->

# CORE BUSINESS PATTERNS (DO NOT VIOLATE)

## 1. No Delete Policy (Nguyên tắc Bất biến)
- **Quy tắc:** Tuyệt đối không bao giờ sử dụng lệnh `DELETE` SQL trên các bảng dữ liệu thực thể chính (`drugs`, `diseases`, `drug_disease_links`).
- **Cơ chế thay thế:**
    - **Soft Delete:** Sử dụng cột `is_active = False` để ẩn dữ liệu khỏi UI/API.
    - **Data Versioning (Lưu kho):** 
        1. Trước khi cập nhật (Update), bản ghi cũ phải được sao lưu sang bảng `_history` hoặc `_warehouse`.
        2. Bản ghi hiện tại được cập nhật `version` và thông tin `updated_by`.

## 2. Staging First (Dữ liệu đệm)
- Mọi dữ liệu thu thập từ bên ngoài (Crawler, CSV Import) không được nhập trực tiếp vào bảng Master.
- Phải đi qua bảng `drug_staging` với trạng thái `PENDING_APPROVAL`.
- Chỉ người dùng có quyền Admin/Pharmacist sau khi thẩm định mới được đẩy dữ liệu từ Staging vào Master.

## 3. Data Integrity & Traceability
- Mọi bản ghi phải có thông tin `created_at` (hệ thống tự sinh) và `created_by` (ID người dùng hoặc 'system_crawler').
- SDK (Số đăng ký) là định danh duy nhất ưu tiên cao nhất cho thuốc. Nếu không có SDK, phải dùng chuỗi băm (hash) từ tên và hoạt chất để nhận diện.

## 4. AI-Inference Priority
- Khi không có liên kết cứng (Verified Link) trong database, hệ thống phải cung cấp dữ liệu từ trường `note` (thẩm định viên) hoặc kết quả `ai_analysis`.
- Kết quả từ AI phải luôn đi kèm với cảnh báo (Disclaimer) và nguồn tham khảo nếu có.