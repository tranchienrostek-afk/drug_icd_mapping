# Quy Trình Thêm Mới API (Standard Process for Adding a New API)

Tài liệu này quy định các bước chuẩn để thêm một API endpoint mới vào dự án `fastapi-medical-app`. Việc tuân thủ quy trình này đảm bảo tính nhất quán, dễ bảo trì và chất lượng của mã nguồn.

## 1. Phân Tích & Thiết Kế (Design Phase)

Trước khi viết code, hãy xác định rõ các thông tin sau:
- **Mục đích**: API này làm gì? (Ví dụ: Tra cứu thuốc, cập nhật thông tin bệnh nhân).
- **Endpoint URL**: Đường dẫn nên theo chuẩn RESTful. (Ví dụ: `/api/v1/drugs/{drug_id}`).
- **HTTP Method**: `GET` (đọc), `POST` (tạo), `PUT` (cập nhật), `DELETE` (xóa).
- **Request Body**: Dữ liệu đầu vào cần những trường nào?
- **Response**: Cấu trúc dữ liệu trả về và các mã lỗi (400, 404, 500).

> [!TIP]
> Hãy tham khảo các API hiện có trong thư mục `app/api/` để giữ sự đồng nhất về cách đặt tên.

## 2. Định Nghĩa Pydantic Models (Model Layer)

Tạo hoặc cập nhật các model trong `app/models.py` (hoặc tạo file mới nếu module quá lớn).
- **Request Model**: Định nghĩa dữ liệu client gửi lên (sử dụng `BaseModel`).
- **Response Model**: Định nghĩa dữ liệu trả về cho client.

```python
# Ví dụ trong app/models.py
from pydantic import BaseModel

class DrugSearchRequest(BaseModel):
    query: str
    limit: int = 10

class DrugResponse(BaseModel):
    id: str
    name: str
    usage: str
```

## 3. Triển Khai Logic Nghiệp Vụ (Service Layer)

Tuyệt đối **không** viết logic phức tạp trực tiếp trong controller (API router). Hãy viết trong `app/service/`.
- Tạo function mới hoặc class mới trong `app/service/`.
- Xử lý các tác vụ như: truy vấn database, gọi LLM, xử lý dữ liệu.

```python
# Ví dụ trong app/service/drug_service.py
def search_drugs(query: str):
    # Logic tìm kiếm thuốc từ database
    pass
```

## 4. Tạo API Router (Controller Layer)

Tạo endpoint trong thư mục `app/api/`. Nếu là module mới, hãy tạo file mới (ví dụ `app/api/new_module.py`).

```python
# Ví dụ trong app/api/drugs.py
from fastapi import APIRouter, Depends
from app.models import DrugSearchRequest, DrugResponse
from app.service import drug_service

router = APIRouter()

@router.post("/search", response_model=list[DrugResponse])
async def search_drugs_api(request: DrugSearchRequest):
    results = drug_service.search_drugs(request.query)
    return results
```

## 5. Đăng Ký Router (Registration)

Nếu bạn tạo một file router mới, hãy nhớ đăng ký nó trong `app/main.py`.

```python
# Trong app/main.py
from app.api import new_module

app.include_router(new_module.router, prefix="/api/v1/new-module", tags=["New Module"])
```

## 6. Kiểm Thử & Xác Nhận (Verification)

- **Manual Test**: Sử dụng Swagger UI tại `/docs` để test thử API bằng tay.
- **Automated Test**: Viết unit test hoặc integration test trong thư mục `scripts/` (ví dụ `scripts/test_new_module.py`).
    - Test case thành công (Happy path).
    - Test case lỗi (Edge cases, invalid input).

## Checklist Trước Khi Submit

- [ ] Đã định nghĩa Request/Response Model rõ ràng.
- [ ] Logic nghiệp vụ được tách biệt khỏi Router.
- [ ] Tên biến và đường dẫn tuân thủ chuẩn naming convention (snake_case cho Python).
- [ ] Đã test thành công trên Swagger UI.
- [ ] Đã xử lý các trường hợp lỗi (Error Handling).
