<!-- Quy tắc viết test -->

# TESTING & QUALITY ASSURANCE RULES

## 1. Testing Framework
- **Framework:** Sử dụng `pytest` kết hợp với `pytest-asyncio`.
- **Test Discovery:** Mọi tệp test phải nằm trong thư mục `tests/` và có tiền tố `test_*.py`.

## 2. Requirements for Tests
- **Isolation:** Mỗi test case phải độc lập. Sử dụng database test riêng hoặc cơ chế `rollback` sau mỗi test.
- **Mocking:** Sử dụng `unittest.mock` hoặc `pytest-mock` để giả lập các service bên ngoài (Azure OpenAI, External Websites) nhằm tránh tốn tài nguyên và đảm bảo tốc độ.
- **Coverage:** Ưu tiên kiểm thử các nhánh logic quan trọng (Edge Cases), đặc biệt là logic xử lý trùng lặp và phân tích AI.

## 3. Async Testing
- Mọi hàm test gọi API hoặc DB phải sử dụng decorator `@pytest.mark.asyncio`.
- Sử dụng `httpx.AsyncClient` để test các endpoint FastAPI.

## 4. Naming Convention for Tests
- Hàm test: `test_<feature_name>_<expected_behavior>` (ví dụ: `test_drug_identify_returns_not_found`).

## 5. Verification Scripts
- Các script kiểm tra nhanh (không phải unit test) được đặt trong thư mục `tests/` nhưng không có tiền tố `test_`. Các script này phục vụ việc kiểm tra dữ liệu thực tế (Real-world data debugging).