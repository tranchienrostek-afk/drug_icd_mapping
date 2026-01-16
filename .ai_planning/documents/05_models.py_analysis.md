# Phân Tích `app/models.py`

File `app/models.py` là nơi định nghĩa toàn bộ **Data Schema** (cấu trúc dữ liệu) cho ứng dụng bằng thư viện **Pydantic**. Các class này đảm bảo dữ liệu đầu vào (Input) từ API là hợp lệ trước khi đi vào logic xử lý, và định hình dữ liệu đầu ra (Output) trả về cho client.

## 1. Input Cơ Bản (Basic Inputs)

Các thành phần nhỏ dùng để tái sử dụng trong các request lớn hơn.

- **`DrugInput`**:
  - Dùng cho thông tin thuốc cơ bản.
  - Trường: `name` (tên thuốc).
  
- **`DiagnosisInput`**:
  - Dùng cho thông tin chẩn đoán bệnh.
  - Trường: `name` (tên bệnh), `icd10` (mã bệnh).

## 2. Request Phân Tích (Analysis Models)

Dùng cho các API phân tích tương tác thuốc và bệnh (ví dụ trong module `app/api/analysis.py`).

- **`AnalysisRequest`**:
  - Input chính cho việc kiểm tra tương tác.
  - Bao gồm danh sách thuốc (`drugs`: list string) và danh sách chẩn đoán (`diagnosis`: list `DiagnosisInput`).
  - Ví dụ: Bệnh nhân bị Tiểu đường (E11) dùng thuốc Panadol.

## 3. Data Management (Quản Lý Dữ Liệu)

Dùng cho các chức năng quản trị, chuẩn hóa và làm sạch dữ liệu (Data Refinery & Staging).

### Staging & Update
- **`DrugConfirmRequest`**: Dữ liệu để xác nhận một thuốc mới vào hệ thống chuẩn.
  - Các trường bắt buộc: `ten_thuoc`, `so_dang_ky`, `hoat_chat`...
- **`DrugStagingUpdateRequest`**: Dùng để cập nhật thông tin thuốc trong bảng tạm (staging). Các trường đều là `Optional` (có thể null).
- **`DrugStagingResponse`**: Cấu trúc trả về khi truy vấn bảng staging, bao gồm thông tin xung đột (`conflict_type`) nếu có.

### Linking (Liên Kết Thuốc - Bệnh)
- **`DrugDiseaseLinkRequest`**:
  - Quan trọng cho việc xây dựng Knowledge Graph.
  - Liên kết một thuốc (`drug_name`, `sdk`) với một bệnh (`disease_name`, `icd_code`).
  - `coverage_type`: Xác định vai trò thuốc (Điều trị chính, Hỗ trợ...).
  - `is_verified`: Đánh dấu dữ liệu đã được kiểm duyệt hay chưa.

## 4. ICD & Disease Management

- **`DiseaseRequest`**: Wrapper đơn giản chứa danh sách bệnh.
- **`DiseaseConfirmRequest`**: Dùng để xác nhận hoặc thêm mới một mã bệnh chuẩn vào hệ thống.

---
**Lưu ý**: Tất cả các class (`BaseModel`) đều có `ConfigDict` chứa `example`. Điều này rất hữu ích vì nó sẽ tự động hiển thị ví dụ mẫu trên giao diện Swagger UI `/docs`, giúp việc test API dễ dàng hơn.
