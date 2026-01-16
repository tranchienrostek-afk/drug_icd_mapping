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
Role: **Raw Interaction Store & Crowd Intelligence Source**

Lưu trữ **mọi tương tác thô** từ các nguồn dữ liệu (CSV Logs từ bệnh viện) để thực hiện chiến lược **"Vote & Promote"**.

### Schema Chi Tiết (v2.1 - Updated 2026-01-16)

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng |
| **Drug Info** | | |
| `drug_name` | TEXT | Tên thuốc gốc từ CSV |
| `drug_name_norm` | TEXT | Tên thuốc chuẩn hóa (lowercase, bỏ dấu) |
| `drug_ref_id` | INTEGER | FK → `drugs.id` (nếu match được) |
| **Primary Disease (Bệnh chính)** | | |
| `disease_icd` | TEXT | Mã ICD bệnh chính (lowercase) |
| `disease_name` | TEXT | Tên bệnh chính gốc |
| `disease_name_norm` | TEXT | Tên bệnh chính chuẩn hóa |
| `disease_ref_id` | INTEGER | FK → `diseases.id` |
| **Secondary Disease (Bệnh phụ)** | | |
| `secondary_disease_icd` | TEXT | Mã ICD bệnh phụ |
| `secondary_disease_name` | TEXT | Tên bệnh phụ gốc |
| `secondary_disease_name_norm` | TEXT | Tên bệnh phụ chuẩn hóa |
| `secondary_disease_ref_id` | INTEGER | FK → `diseases.id` |
| **Classification** | | |
| `treatment_type` | TEXT | Phân loại từ AI (e.g. `drug, main`) |
| `tdv_feedback` | TEXT | Feedback từ TDV (e.g. `drug`) |
| `symptom` | TEXT | Chẩn đoán ra viện (giữ nguyên) |
| `prescription_reason` | TEXT | Lý do kê đơn |
| **Metadata** | | |
| `frequency` | INTEGER | Số lần xuất hiện (Vote Count). Mặc định: 1 |
| `confidence_score` | REAL | Điểm tin cậy. Mặc định: 0.0 |
| `batch_id` | TEXT | ID của batch CSV import |
| `last_updated` | TIMESTAMP | Thời điểm cập nhật cuối |

### Classification Columns

Thay vì gộp chung, giờ đây hệ thống lưu 2 cột riêng biệt:
- **`treatment_type`**: Input từ cột **Phân loại** (AI Classification)
- **`tdv_feedback`**: Input từ cột **Feedback** (Chuyên gia thẩm định)

### Các Index Quan Trọng

```sql
CREATE INDEX idx_kb_lookup ON knowledge_base(drug_name_norm, disease_name_norm);
CREATE INDEX idx_kb_type ON knowledge_base(treatment_type);
CREATE INDEX idx_kb_icd ON knowledge_base(disease_icd);
```

## 3. CSV Import Mapping

| Cột CSV | Xử lý | Cột DB |
|---------|-------|--------|
| Tên thuốc | Lưu gốc + normalize | `drug_name`, `drug_name_norm` |
| Mã ICD (Chính) | Parse "CODE - Name" | `disease_icd`, `disease_name`, `disease_name_norm` |
| Bệnh phụ | Parse "CODE - Name" | `secondary_disease_*` |
| Chẩn đoán ra viện | Giữ nguyên | `symptom` |
| Phân loại | Giữ nguyên | `treatment_type` (AI) |
| Feedback | Giữ nguyên | `tdv_feedback` (TDV) |
| Lý do kê đơn | Giữ nguyên | `prescription_reason` |
| Cách dùng | ⏭️ Bỏ qua | - |
| SL | ⏭️ Bỏ qua | - |

## 4. Logic "Vote & Promote"

Quy trình xác định phân loại cho cặp `(Thuốc A, Bệnh B)`:

1. **Query**: `SELECT treatment_type, tdv_feedback, COUNT(*) as vote_count FROM knowledge_base WHERE drug_name_norm = ? AND disease_icd = ? GROUP BY treatment_type, tdv_feedback`
2. **Decision**: Ưu tiên theo `tdv_feedback` nếu có, sau đó đến `treatment_type` có vote cao nhất.

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-16 | 2.0.0 | Thêm: `drug_name`, `secondary_disease_*`, `symptom`, `prescription_reason`. Format mới cho `treatment_type`. |
| 2026-01-15 | 1.0.0 | Initial schema |
