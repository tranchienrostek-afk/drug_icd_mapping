<!-- Quy tắc đặt tên, Type hints, Comments -->

# CODING STYLE GUIDELINES

## 1. Naming Conventions (Quy chuẩn đặt tên)
- **Variables/Functions:** `snake_case` (ví dụ: `get_drug_by_sdk`).
- **Classes:** `PascalCase` (ví dụ: `DrugService`, `DiseasesRepository`).
- **Constants/Enums:** `UPPER_CASE` (ví dụ: `MAX_RETRIES`, `DRUG_STATUS_PENDING`).
- **Private methods/vars:** Bắt đầu bằng gạch dưới `_` (ví dụ: `_calculate_hash`).
- **Boolean variables:** Nên bắt đầu bằng prefixes như `is_`, `has_`, `can_` (ví dụ: `is_verified`).

## 2. Type Hinting (MANDATORY - BẮT BUỘC)
- 100% chữ ký hàm (function signature) phải có Type Hints đầy đủ cho cả tham số đầu vào và kết quả trả về.
- Sử dụng các kiểu dữ liệu từ `typing` hoặc native (Python 3.10+).
- **Bad:** `def update_status(drug_id, status):`
- **Good:** `def update_status(drug_id: str, status: DrugStatus) -> bool:`

## 3. Docstrings & Comments
- Sử dụng **Google Style Docstrings** cho mọi class và public function.
- Phải mô tả đầy đủ: `Args`, `Returns` và `Raises`.
- Chỉ comment "Tại sao" (Why), không comment "Cái gì" (What) trừ khi đoạn code cực kỳ phức tạp.

## 4. Error Handling
- Không bao giờ sử dụng `try: ... except: pass` (Bare except).
- Luôn raise các exception có ý nghĩa (Custom Exceptions) cho business logic.
- Log lỗi đầy đủ traceback sử dụng thư viện `logging`.

## 5. Pydantic Usage
- Sử dụng `SecretStr` cho các thông tin nhạy cảm.
- Sử dụng `AliasPath` hoặc `Field(alias=...)` khi làm việc với API bên ngoài có naming convention khác.