# Định nghĩa Enum (Enumeration Definitions)

Tài liệu này liệt kê các giá trị hợp lệ cho các trường trạng thái và phân loại trong hệ thống.

## 1. Trạng thái bản ghi (Record Status)
Dùng chung cho nhiều bảng (ví dụ: `drugs`, `diseases`).
- `active`: Đang hoạt động, được phép tìm kiếm và hiển thị.
- `inactive`: Bị vô hiệu hóa, không sử dụng.

## 2. Trạng thái Staging (`drug_staging.status`)
- `pending`: Dữ liệu mới được cào về hoặc nhập vào, đang chờ kiểm duyệt.
- `approved`: Đã được chấp thuận và chuyển vào bảng chính (`drugs`).
- `rejected`: Đã bị từ chối do sai lệch dữ liệu.

## 3. Loại xung đột (`drug_staging.conflict_type`)
- `sdk`: Xung đột trùng Số đăng ký.
- `name`: Xung đột trùng tên thuốc (khi không có SDK).

## 4. Hành động lịch sử (`drug_staging_history.action`)
- `rejected`: Bị từ chối.
- `cleared`: Đã được xóa khỏi staging sau khi xử lý.
- `approved`: Đã được phê duyệt.

## 5. Trạng thái xác minh (`is_verified`)
Dùng trong `drugs` và `drug_disease_links`.
- `0`: Chưa xác minh (Dữ liệu từ máy hoặc crawler).
- `1`: Đã xác minh bởi dược sĩ/chuyên gia.

## 6. Trạng thái liên kết (`drug_disease_links.status`)
- `active`: Liên kết có hiệu lực.
- `pending`: Liên kết chờ duyệt (thường đi kèm với thuốc chờ duyệt).
- `archived`: Liên kết cũ hoặc bị từ chối/xóa.

## 7. Loại bao phủ (`drug_disease_links.coverage_type`)
- `Thuốc điều trị`: Thuốc chính điều trị nguyên nhân.
- `Thuốc hỗ trợ`: Thuốc điều trị triệu chứng hoặc bổ trợ.
- `Thay thế`: Thuốc thay thế khi dị ứng hoặc không đáp ứng.
