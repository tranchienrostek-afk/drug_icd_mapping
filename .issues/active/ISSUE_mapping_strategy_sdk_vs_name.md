# Issue: Chiến lược Mapping Thuốc (SĐK vs Tên Chuẩn Hóa)

**Ngày tạo**: 14/01/2026
**Trạng thái**: Open
**Độ ưu tiên**: Medium

## Mô Tả Vấn Đề
Hiện tại hệ thống đang sử dụng 2 cơ chế mapping thuốc khác nhau cho 2 luồng nghiệp vụ, gây ra sự không nhất quán về logic định danh:

1.  **Consultation API (`/api/v1/consult_integrated`)**:
    -   Sử dụng **Tên thuốc chuẩn hóa (Normalized Name)** làm khoá chính để tra cứu `knowledge_base`.
    -   Lý do hiện tại: Tối ưu cho dữ liệu nhập tay từ người dùng (thường thiếu SĐK).

2.  **Analysis API (`/api/v1/analysis`)**:
    -   Sử dụng **Số Đăng Ký (SĐK)** làm khoá chính để tra cứu `drug_disease_links`.
    -   Lý do hiện tại: Đảm bảo độ chính xác tuyệt đối với dữ liệu đã xác thực.

## Yêu Cầu Cần Xem Xét
Cần đánh giá lại xem có nên thống nhất logic mapping cho **Consultation API** hay không. Cụ thể:
-   Nếu đầu vào có SĐK -> Ưu tiên tìm theo SĐK (Chính xác 100%).
-   Nếu không tìm thấy theo SĐK hoặc không có SĐK -> Mới Fallback về tìm theo Tên chuẩn hóa.

## File Liên Quan
-   `app/api/consult.py`
-   `app/services.py` (DrugDbEngine)
