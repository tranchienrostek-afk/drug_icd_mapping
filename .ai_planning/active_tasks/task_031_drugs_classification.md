# Kế hoạch Chi Tiết: Phân Loại Thuốc & Tích Hợp API (Task 031)

## 1. Mục Tiêu
Triển khai hệ thống "Medical Intelligence Gateway" theo kiến trúc "Vote & Promote", bao gồm 2 API chính:
1.  **Ingest API**: Nhập liệu log giao dịch y tế (Drug/Disease) từ thiết bị ngoại vi, xử lý bất đồng bộ để xây dựng Knowledge Base (KB).
2.  **Consult API**: API tư vấn tích hợp, ưu tiên sử dụng tri thức từ KB (High Confidence) trước khi gọi AI bên thứ 3.

## 2. Thiết Kế Cơ Sở Dữ Liệu (SQLite)
Mở rộng `app/services.py` -> `DrugDbEngine` để hỗ trợ các bảng sau:

### 2.1. `raw_logs` (Lưu vết dữ liệu thô)
*   **Mục đích**: Lưu trữ nguyên vẹn dữ liệu gửi lên để Audit và Re-training.
*   **Columns**:
    *   `id` (PK)
    *   `batch_id`: Mã lô nhập liệu.
    *   `raw_content`: JSON/CSV content gốc.
    *   `created_at`: Thời gian nhận.
    *   `source_ip`: Nguồn gửi.

### 2.2. `knowledge_base` (Tri thức đám đông - Tần suất)
*   **Mục đích**: "Bộ não" của hệ thống, lưu trữ tần suất xuất hiện của các cặp (Thuốc - Bệnh).
*   **Columns**:
    *   `id` (PK)
    *   `drug_name_norm`: Tên thuốc chuẩn hóa (Lowercase, remove accents).
    *   `drug_ref_id`: (FK) ID thuốc trong bảng `drugs` (nếu map được).
    *   `disease_name_norm`: Tên bệnh chuẩn hóa.
    *   `disease_icd`: Mã ICD (nếu có).
    *   `frequency`: Số lần xuất hiện (Counter).
    *   `confidence_score`: Điểm tin cậy (0.0 - 1.0).
    *   `last_updated`: Thời gian cập nhật gần nhất.

## 3. Chi Tiết Thực Thi (Implementation Steps)

### Giai Đoạn 1: Nâng Cấp Database & Core
- [ ] **Bước 1.1**: Cập nhật `DrugDbEngine._ensure_tables` trong `app/services.py` để tạo bảng `raw_logs` và `knowledge_base`.
- [ ] **Bước 1.2**: Viết hàm `upsert_knowledge_base(drug, disease)`:
    - Nếu cặp (drug, disease) đã tồn tại -> Tăng `frequency` + Update `confidence_score`.
    - `confidence_score` = log(frequency) / max_log (Logic đơn giản ban đầu).

### Giai Đoạn 2: Xây Dựng Ingest API (API 1)
- [ ] **Bước 2.1**: Tạo file `app/api/data_management.py`.
- [ ] **Bước 2.2**: Định nghĩa Endpoint `POST /api/v1/ingest`.
    - Input: Upload File (CSV).
    - Logic:
        1. Lưu file/nội dung vào `raw_logs`.
        2. Trigger Background Task (`FastAPI.BackgroundTasks`).
    - Output: `{"task_id": "...", "status": "processing"}`.
- [ ] **Bước 2.3**: Triển khai ETL Service (`app/service/etl_service.py`):
    - Đọc `raw_logs`.
    - Loop qua từng dòng:
        - Chuẩn hóa tên thuốc/bệnh.
        - Gọi `upsert_knowledge_base`.

### Giai Đoạn 3: Xây Dựng Consult API (API 2)
- [ ] **Bước 3.1**: Tạo file `app/api/consult.py` (hoặc tích hợp vào `analysis.py`).
- [ ] **Bước 3.2**: Định nghĩa Endpoint `POST /api/v1/consult_integrated`.
    - Input: Danh sách thuốc (`items`) + Danh sách bệnh (`diagnoses`).
- [ ] **Bước 3.3**: Logic xử lý (Hybrid Flow):
    - **Step 1 (Check KB)**: Query `knowledge_base` với cặp `(drug, disease)`.
        - Nếu `confidence_score > THRESHOLD` (VD: 0.8) -> Return kết quả ngay (Source: Internal).
    - **Step 2 (Fallback)**: Nếu Step 1 fail -> Gọi `patched_llm.analyze_treatment_group` (Source: External AI).
- [ ] **Bước 3.4**: Standardize Output format:
    - Cấu trúc đồng nhất cho cả Internal và External result để FE dễ hiển thị.

## 4. Kế Hoạch Kiểm Thử (Verification)
### 4.1. Ingestion Test
- Tạo file CSV giả lập: 100 dòng "Panadol" - "Đau đầu".
- Gọi API Ingest.
- Kiểm tra DB `knowledge_base`: Record "panadol"-"đau đầu" phải có `frequency` = 100.

### 4.2. Consult Test
- **Case 1 (High Confidence)**: Gửi request "Panadol" + "Đau đầu".
    - Kỳ vọng: Trả về ngay lập tức, `source`="Internal".
- **Case 2 (Low Confidence/New)**: Gửi request "Thuốc Lạ ABC" + "Bệnh Hiếm XYZ".
    - Kỳ vọng: Hệ thống gọi External AI và trả về kết quả từ AI, `source`="External AI".

## 5. Tài Liệu Tham Khảo
- `rules for knowledge.md`: Tuân thủ quy tắc bảo toàn tri thức gốc.
- `logs_to_database/solution.md`: Logic Vote & Promote.
