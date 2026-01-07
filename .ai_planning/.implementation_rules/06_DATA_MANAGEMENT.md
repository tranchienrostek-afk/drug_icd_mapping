# DATA MANAGEMENT & ICD-10 STANDARDS

Tài liệu này quy định cách xử lý và chuẩn hóa dữ liệu thuốc và bệnh lý.

## 1. Dữ liệu Thuốc (Drug Data)
- **Tên thuốc:** Luôn normalize về dạng INHOA (ví dụ: PANADOL -> PANADOL).
- **Hàm lượng:** Tách biệt rõ ràng giá trị và đơn vị (ví dụ: 500mg -> `value: 500, unit: mg`).
- **Số đăng ký (SDK):** Phải làm sạch các ký tự đặc biệt, dấu cách thừa. Định dạng chuẩn hóa là `ABC-12345-67`.

## 2. Bệnh lý (ICD-10)
- **Mã ICD:** Luôn lưu ở dạng rút gọn (Short code) và đầy đủ (Full code).
- **Ngôn ngữ:** Ưu tiên Tiếng Việt chính thống theo quy định của Bộ Y tế. Dự phòng Tiếng Anh cho nghiên cứu.
- **Cấu trúc:** Phải duy trì liên kết phân cấp (Chapter -> Group -> Disease).

## 3. Quy trình Trình trích xuất (Extraction)
- **Web Crawler:** Phải thực hiện trích xuất đa nguồn (Cross-source validation).
- **Xử lý Null:** Nếu một trường dữ liệu bắt buộc bị thiếu, phải gắn tag `DATA_MISSING` để yêu cầu Pharmacist bổ sung.

## 4. Tri thức liên kết (Knowledge Graph)
- Mối quan hệ giữa Thuốc và Bệnh được định nghĩa theo các mức độ:
    - **Verified:** Có bằng chứng lâm sàng/Dược thư.
    - **Pending:** Đang chờ AI hoặc Chuyên gia xác nhận.
    - **Refused:** Đã bị từ chối do chống chỉ định.
迫
