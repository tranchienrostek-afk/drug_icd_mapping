# Domain: Knowledge Graph (Links)

Thông tin liên kết giữa thuốc và bệnh tật, hỗ trợ hệ thống gợi ý và phân tích điều trị.

## 1. Bảng `drug_disease_links`
Lưu trữ các liên kết "Thuốc - Điều trị - Bệnh".

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng |
| `drug_id` | INTEGER | ID thuốc (FK sang `drugs.id`) |
| `disease_id` | INTEGER | ID bệnh (FK sang `diseases.id`) |
| `sdk` | TEXT | Lưu lại SDK tại thời điểm liên kết |
| `icd_code` | TEXT | Lưu lại mã ICD tại thời điểm liên kết |
| `treatment_note`| TEXT | Diễn giải chi tiết về cách dùng/hiệu quả |
| `coverage_type` | TEXT | Phân loại liên kết (ví dụ: 'chính', 'phụ') |
| `is_verified` | INTEGER | Trạng thái xác thực bởi chuyên gia |
| `status` | TEXT | 'active' hoặc 'inactive' |

## 2. Logic Phân tích
AI sử dụng dữ liệu trong bảng này làm "Ground Truth" (Sự thật gốc) để đối chiếu khi phân tích các đơn thuốc hoặc phác đồ điều trị mới.
- Nếu `is_verified = 1`: Tin cậy tuyệt đối.
- Nếu `is_verified = 0`: Cần thẩm định lại hoặc đánh giá qua AI Inference.
迫
