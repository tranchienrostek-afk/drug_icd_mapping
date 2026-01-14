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

Thay vì lưu trữ dữ liệu đã gộp (aggregated), bảng này lưu trữ **mọi tương tác thô** (Raw Interactions) hợp lệ từ các nguồn dữ liệu (CSV Logs từ bệnh viện).
Điều này cho phép hệ thống thực hiện chiến lược **"Vote & Promote"**:
- Mỗi bản ghi là một "phiếu bầu" (Vote) của một bác sĩ/thẩm định viên cho cách phân loại thuốc-bệnh đó.
- Khi truy vấn (Consult), hệ thống sẽ đếm phiếu (Count) và trả về kết quả được bầu chọn nhiều nhất.

### Schema Chi Tiết

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng |
| `drug_name_norm` | TEXT | Tên thuốc đã chuẩn hóa (Dùng để tìm kiếm/nhóm). Ví dụ: "panadol" |
| `disease_name_norm`| TEXT | Tên bệnh đã chuẩn hóa (Dùng để tìm kiếm/nhóm). Ví dụ: "viêm mũi họng" |
| `raw_drug_name` | TEXT | Tên thuốc nguyên bản từ nguồn (vd: "Panadol Extra 500mg"). Giúp audit. |
| `raw_disease_name` | TEXT | Tên bệnh nguyên bản từ nguồn (vd: "Viêm họng cấp J02"). Giúp audit. |
| `treatment_type` | TEXT | Phân loại điều trị (The "Vote"). **Standard Values** (match `group_definitions.md`): `valid` (Thuốc chính), `secondary drug`, `medical supplies`, `supplement`, `cosmeceuticals`, `medical equipment`, `invalid`. |
| `disease_icd` | TEXT | Mã ICD tham chiếu từ nguồn (nếu có). |
| `source_id` | TEXT | Định danh nguồn dữ liệu (vd: `batch_id` từ lần import CSV). |
| `confidence_score` | REAL | Trọng số của nguồn dữ liệu này (Mặc định: 1.0). Có thể dùng để ưu tiên nguồn uy tín hơn. |
| `created_at` | TIMESTAMP | Thời điểm bản ghi được tạo. |

### Các Index Quan Trọng
1.  `idx_kb_lookup(drug_name_norm, disease_name_norm)`: Index cốt lõi phục vụ truy vấn Consult.
2.  `idx_kb_type(treatment_type)`: Hỗ trợ thống kê, báo cáo theo loại điều trị.

## 3. Logic "Vote & Promote"
Quy trình xác định phân loại cho cặp `(Thuốc A, Bệnh B)`:

1.  **Query**: `SELECT treatment_type, COUNT(*) as vote_count FROM knowledge_base WHERE drug_name_norm = ? AND disease_name_norm = ? GROUP BY treatment_type`
2.  **Decision**: Chọn `treatment_type` có `vote_count` cao nhất.
3.  **Confidence**: `Score = vote_count / total_votes`.

Ví dụ:
- 90 votes: `valid`
- 5 votes: `secondary drug`
- 2 votes: `supplement`
=> Kết luận: Link này là **valid** (Thuốc chính) (Confidence ~92%).

