# Quy Trình Debug API (API Debugging Workflow)

Tài liệu này hướng dẫn quy trình tiêu chuẩn để điều tra và xử lý lỗi API trong dự án `fastapi-medical-app`.

## 1. Thu Thập & Phân Tích Logs (Log Analysis)

Bước đầu tiên là phải biết lỗi gì đang xảy ra.

- **Checklogs Server**: Xem logs của uvicorn/fastapi.
    ```bash
    # Nếu chạy docker
    docker logs -f <container_id>
    
    # Nếu chạy local
    # Logs thường hiển thị trực tiếp trên terminal
    ```
- **Tìm kiếm Keyword**: Tìm các từ khóa như `ERROR`, `Traceback`, `Exception`, `500 Internal Server Error`.
- **Xác định Request ID**: Nếu hệ thống có logging middleware, hãy tìm `request_id` để trace toàn bộ dòng chảy của request đó.

## 2. Tái Hiện Lỗi (Reproduction)

Đừng cố sửa lỗi nếu bạn chưa thể tái hiện nó.

- **Local Reproduction**:
    1. Lấy mẫu payload (dữ liệu gửi lên) gây lỗi.
    2. Sử dụng Swagger UI (`/docs`) hoặc Postman để gửi lại request đó.
    3. Nếu lỗi liên quan đến logic phức tạp, hãy viết một script nhỏ trong thư mục `scripts/` để gọi hàm service trực tiếp.
    
    ```python
    # Ví dụ: scripts/reproduce_issue.py
    from app.service.drug_service import search_drugs
    
    # Giả lập input gây lỗi
    search_drugs(query="thuốc gây lỗi")
    ```

## 3. Phân Lập Nguyên Nhân (Problem Isolation)

Xác định xem lỗi đến từ đâu:
- **Lỗi Data**: Dữ liệu đầu vào sai format, thiếu trường? Hay dữ liệu trong DB bị bẩn?
- **Lỗi Code Logic**: Thuật toán sai, xử lý null sai?
- **Lỗi External Service**: Gọi LLM bị timeout? Database bị quá tải?
- **Lỗi Môi Trường**: Thiếu biến môi trường `.env`? Phiên bản thư viện không khớp?

## 4. Sửa Lỗi & Kiểm Tra (Fix & Verify)

- **Viết Test Case Trước**: Tốt nhất là viết một test case (trong `scripts/test_*.py`) mà nó *fail* với lỗi hiện tại.
- **Thực Hiện Sửa Lỗi**: Sửa code.
- **Chạy Lại Test Case**: Đảm bảo test case chuyển sang *pass*.
- **Regression Test**: Chạy lại các test case liên quan khác để đảm bảo không làm hỏng các tính năng cũ.

## Các Công Cụ Hữu Ích

| Công Cụ | Mục Đích |
| :--- | :--- |
| **Swagger UI** (`/docs`) | Test API nhanh, xem document. |
| **Postman / Curl** | Test API nâng cao, giả lập header, auth phức tạp. |
| **DB Browser for SQLite** | Kiểm tra trực tiếp dữ liệu trong `medical.db`. |
| **VS Code Debugger** | Đặt breakpoint và chạy từng dòng code (F5). |

> [!IMPORTANT]
> Luôn luôn đọc kỹ thông báo lỗi (Error Message). 90% câu trả lời nằm ngay trong dòng đầu tiên hoặc dòng cuối cùng của Traceback.
