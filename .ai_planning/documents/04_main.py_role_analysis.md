# Phân Tích Vai Trò của `app/main.py`

File `app/main.py` đóng vai trò là xương sống (backbone) và là điểm khởi chạy chính (entry point) của toàn bộ ứng dụng `fastapi-medical-app`. Nơi đây tập trung cấu hình, kết nối các thành phần và định tuyến request.

## 1. Khởi Tạo Ứng Dụng (Initialization)

```python
app = FastAPI(title="Medical API System", version="1.0.0")
```
- Khởi tạo instance `FastAPI` chính.
- Thiết lập tiêu đề và phiên bản cho Swagger UI (`/docs`).

## 2. Đăng Ký Middleware (Middleware)

```python
from app.middlewares.logging_middleware import LogMiddleware
app.add_middleware(LogMiddleware)
```
- **Logging Middleware**: Hệ thống đăng ký `LogMiddleware` để ghi lại mọi request đến và response đi, giúp cho việc debug và monitoring.

## 3. Cấu Hình Static Files

```python
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```
- Mount thư mục `app/static/` ra đường dẫn URL `/static`.
- Cho phép truy cập trực tiếp các file tĩnh như hình ảnh, CSS, JS hoặc `index.html`.

## 4. Đăng Ký Router (Routing)

Đây là phần quan trọng nhất, nơi `main.py` gom các module API con lại thành một hệ thống thống nhất.

| Prefix URL | Module | Vai Trò |
| :--- | :--- | :--- |
| `/api/v1/drugs` | `drugs.router` | Tra cứu, quản lý thông tin thuốc. |
| `/api/v1/diseases` | `diseases.router` | Tra cứu mã bệnh ICD và thông tin bệnh học. |
| `/api/v1/analysis` | `analysis.router` | Các API phân tích dữ liệu chuyên sâu. |
| `/api/v1/admin` | `admin.router` | Các tác vụ quản trị hệ thống. |
| `/api/v1/data` | `data_management.router` | Import/Export và quản lý dữ liệu thô. |
| `/api/v1` | `consult.router` | Chatbot tư vấn và các tính năng hỗ trợ người dùng khác. |

## 5. Root Endpoint

```python
@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))
```
- Khi truy cập vào trang chủ (root URL `/`), hệ thống sẽ trả về file `index.html` từ thư mục static, đóng vai trò là giao diện frontend mặc định.

---
**Tóm lại**: `main.py` không nên chứa logic nghiệp vụ phức tạp. Nhiệm vụ của nó chỉ là "lắp ráp" các mảnh ghép (routers, middlewares, config) lại với nhau để ứng dụng có thể chạy được.
