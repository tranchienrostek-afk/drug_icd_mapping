# Phân Tích `app/api/drugs.py`

File `app/api/drugs.py` đóng vai trò là **API Controller** cho các chức năng liên quan đến thuốc. Tuy nhiên, hiện tại nó đang vi phạm nguyên tắc "Thin Controller, Fat Service" (Controller mỏng, Service dày) ở một số điểm quan trọng.

## 1. Cấu Trúc Hiện Tại
- Sử dụng `APIRouter` để định nghĩa các endpoint.
- Gọi đến `DrugDbEngine` (hiện là Facade) để xử lý dữ liệu.
- Import trực tiếp các model Pydantic (`DrugRequest`, `DrugConfirmRequest`...).

## 2. Vấn Đề: Lẫn Lộn Logic Nghiệp Vụ (Business Logic Leakage)

Endpoint `@router.post("/identify")` (dòng 92-183) đang chứa quá nhiều logic xử lý phức tạp, thay vì chỉ làm nhiệm vụ điều hướng:

1.  **Normalization Logic (Dòng 104-109)**:
    - Việc gọi `normalize_drug_name` và quyết định thay thế keyword nên nằm ở Service layer, không phải ở Controller.

2.  **Chiến Lược Tìm Kiếm (Search Strategy - Dòng 114-165)**:
    - Logic quyết định khi nào dùng Database, khi nào fallback sang Web Search ("If confidence > 95% stop, else search web") là logic nghiệp vụ cốt lõi.
    - Controller không nên biết về "confidence threshold" hay quy trình fallback.

3.  **Xử Lý Dữ Liệu Thô (Web Scraping Integration - Dòng 146-160)**:
    - Controller đang trực tiếp gọi `scrape_drug_web` và map dữ liệu thô vào format trả về.
    - Nếu logic scraping thay đổi, ta phải sửa file API -> Sai nguyên tắc.

4.  **Kiểm Tra Trùng Lặp (Duplicate Detection - Dòng 95 & 168-175)**:
    - Logic `seen_sdk` để filter trùng lặp trong một batch request cũng là logic xử lý dữ liệu.

## 3. Đề Xuất Refactoring (Cải Tiến)

Cần tách toàn bộ logic trong `/identify` ra một Service riêng, ví dụ `DrugIdentificationService` hoặc đưa vào `DrugSearchService`.

**Mục tiêu**: API Controller sẽ chỉ còn đơn giản như sau:

```python
@router.post("/identify")
async def identify_drugs(payload: DrugRequest):
    # Controller chỉ nhận request và gọi Service
    results = await drug_identification_service.process_batch(payload.drugs)
    return {"results": results}
```

**Các Endpoint Khác**:
- `/admin/staging`, `/confirm`, `/admin/approve`: Đã khá gọn, chỉ gọi trực tiếp `db.function()`. Tuy nhiên, vẫn đang phụ thuộc vào `DrugDbEngine` cũ thay vì các service mới (`DrugApprovalService`).

## Kết Luận
File này cần được Refactor ở **Giai đoạn 2** (sau khi đã ổn định các Service core) để chuyển hết logic nghiệp vụ về đúng nơi quy định (`app/service/`).
