# Domain: Knowledge Graph & Connectors

Lưu trữ các mối quan hệ, liên kết giữa Thuốc và Bệnh, cùng với Knowledge Base hỗ trợ thuật toán gợi ý.

## 1. Bảng `drug_disease_links`
Lưu trữ các liên kết cứng (Explicit Links) giữa Thuốc và Bệnh.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng |
| `drug_id` | INTEGER | FK sang `drugs.id` (có thể null nếu thuốc chưa vào DB chính) |
| `disease_id` | INTEGER | FK sang `diseases.id` |
| `sdk` | TEXT | SDK thuốc (Snapshot tại thời điểm link) |
| `icd_code` | TEXT | Mã ICD bệnh (Snapshot) |
| `treatment_note` | TEXT | Ghi chú điều trị (vd: Liều dùng, lưu ý) |
| `coverage_type` | TEXT | Loại liên kết: `Thuốc chính`, `Thuốc hỗ trợ`, v.v. |
| `is_verified` | INTEGER | 1 = Đã kiểm duyệt chuyên môn, 0 = Chưa |
| `status` | TEXT | `active` (hiệu lực), `pending` (chờ duyệt), `archived` |
| `created_by` | TEXT | Người tạo link |
| `created_at` | TIMESTAMP | Thời điểm tạo |

## 2. Bảng `knowledge_base`
Bảng tri thức tổng hợp (Implicit Knowledge) dùng cho thuật toán **Vote & Promote**. Lưu trữ tần suất xuất hiện của các cặp Thuốc-Bệnh từ dữ liệu lịch sử/ETL.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng |
| `drug_name_norm` | TEXT | Tên thuốc đã chuẩn hóa (key lookup) |
| `disease_name_norm`| TEXT | Tên bệnh đã chuẩn hóa (key lookup) |
| `drug_ref_id` | INTEGER | Reference ID tới bảng drugs (nếu có) |
| `disease_icd` | TEXT | Mã ICD tham chiếu |
| `frequency` | INTEGER | Số lần cặp này xuất hiện trong dữ liệu huấn luyện |
| `confidence_score` | REAL | Điểm tin cậy tính toán (ví dụ: Logarithmic scale của frequency) |
| `last_updated` | TIMESTAMP | Thời điểm cập nhật cuối cùng |

**Index**: `idx_kb_lookup(drug_name_norm, disease_name_norm)` - Giúp truy vấn O(1).
