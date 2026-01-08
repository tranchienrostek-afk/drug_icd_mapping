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

## MERGE
# TESTING RULES & TDD WORKFLOW
**Framework:** `pytest`
**Mocking:** `unittest.mock` hoặc `pytest-mock`

## Quy trình TDD bắt buộc (Red-Green-Refactor)
1.  **RED (Viết Test trước):** Trước khi viết bất kỳ logic nào, phải viết một Test Case mô tả hành vi mong muốn. Test này **phải fail** ban đầu.
2.  **GREEN (Implement):** Viết code logic tối thiểu (minimal code) để test chuyển sang màu xanh (Pass). Không viết dư thừa (YAGNI).
3.  **REFACTOR:** Tối ưu hóa code sau khi đã pass test.

## Cấu trúc Test
- Tên file test: `tests/test_<module_name>.py`
- Tên hàm test: `test_<function_name>_<scenario>`
- Mỗi test case phải độc lập (Isolated).