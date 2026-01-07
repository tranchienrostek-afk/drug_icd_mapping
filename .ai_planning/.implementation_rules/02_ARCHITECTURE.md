<!-- Pattern dự án (Service Layer, Repository,...) -->

# SYSTEM ARCHITECTURE PATTERNS

## 1. Layered Architecture (Kiến trúc phân lớp)
Mọi component phải tuân thủ phân lớp nghiêm ngặt để đảm bảo khả năng bảo trì:

### API Layer (`app/api/`)
- Trách nhiệm: Định nghĩa endpoint, parse payload, validate schema.
- Ràng buộc: Chỉ gọi Service Layer. Tuyệt đối không query DB hoặc xử lý logic phức tạp.

### Service Layer (`app/services/`)
- Trách nhiệm: Thực thi Business Logic cốt lõi (ví dụ: logic hợp nhất thuốc, xử lý kết quả crawler).
- Ràng buộc: Gọi Repository để truy xuất dữ liệu. Có thể gọi các Service khác.

### Repository/DAO Layer (`app/models/` hoặc `app/repository/`)
- Trách nhiệm: Thực hiện các câu lệnh SQL/Cypher trực tiếp.
- Ràng buộc: Chỉ chứa các query "thuần", không chứa logic kiểm tra nghiệp vụ.

## 2. Dependency Injection (DI)
- Sử dụng cơ chế `Depends` của FastAPI để inject dependencies.
- Tách biệt rõ ràng instance của Repository và Service.

## 3. Configuration Management
- Mọi cấu hình phải nằm trong `app/core/config.py` (sử dụng `pydantic-settings`).
- Không hardcode bất kỳ tham số nào trong code logic.

## 4. DTO & Schema Pattern
- Sử dụng Pydantic models (Schemas) để trao đổi dữ liệu giữa API và Service.
- Không trả trực tiếp SQLAlchemy model ra ngoài API Layer.