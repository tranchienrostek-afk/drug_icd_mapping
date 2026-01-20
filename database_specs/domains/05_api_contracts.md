# Domain: API Contracts

Định nghĩa các API Endpoints của hệ thống Medical API.

**Base URL**: `/api/v1`

---

## 1. Health Check

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/api/v1/health` | Kiểm tra trạng thái hệ thống |

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "ok",
  "services": {
    "drug_search": "available",
    "consultation": "available",
    "crawler": "available"
  }
}
```

---

## 2. Drugs API (`/api/v1/drugs`)

### 2.1. Drug Retrieval

| Method | Path | Mô tả | Auth |
|--------|------|-------|------|
| `GET` | `/` | Lấy danh sách thuốc (phân trang) | - |
| `GET` | `/{row_id}` | Lấy chi tiết thuốc theo ID | - |

**Query Params** (`GET /`):
- `page`: int (default: 1)
- `limit`: int (default: 10)
- `search`: string (optional)

### 2.2. Drug Identification

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/identify` | Nhận dạng thuốc (DB + Web fallback) |
| `POST` | `/agent-search` | Tìm kiếm thuốc qua AI Agent (Browser) |

**Request Body** (`/identify`, `/agent-search`):
```json
{
  "drugs": ["Paracetamol 500mg", "Amoxicillin 250mg"]
}
```

### 2.3. Drug Administration

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/confirm` | Lưu thuốc đã xác minh vào DB |
| `POST` | `/knowledge/link` | Tạo liên kết Thuốc-Bệnh |

**Request Body** (`/confirm`):
```json
{
  "ten_thuoc": "Panadol Extra",
  "so_dang_ky": "VN-12345-67",
  "hoat_chat": "Paracetamol, Caffeine",
  "chi_dinh": "Giảm đau, hạ sốt",
  "cong_ty_san_xuat": "GSK"
}
```

### 2.4. Staging Management

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/admin/staging` | Lấy danh sách thuốc chờ duyệt |
| `POST` | `/admin/approve/{staging_id}` | Duyệt thuốc từ Staging → Main |
| `POST` | `/admin/reject/{staging_id}` | Từ chối thuốc (Soft Delete) |
| `PUT` | `/admin/staging/{staging_id}` | Chỉnh sửa thuốc trong Staging |
| `POST` | `/admin/staging/clear` | Xóa toàn bộ Staging → History |

---

## 3. Diseases API (`/api/v1/diseases`)

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/lookup` | Tra cứu thông tin bệnh theo ICD-10 |

**Request Body**:
```json
{
  "diagnosis": [
    { "name": "Đau đầu", "icd10": "R51" }
  ]
}
```

---

## 4. Analysis API (`/api/v1/analysis`)

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/treatment-analysis` | Phân tích điều trị (Thuốc + Bệnh → AI) |

**Request Body**:
```json
{
  "drugs": ["Candesartan 16mg", "Paracetamol 500mg"],
  "diagnosis": [
    { "name": "Tăng huyết áp", "icd10": "I10" },
    { "name": "Đau đầu", "icd10": "R51" }
  ]
}
```

**Response**:
```json
{
  "drugs_info": [...],
  "diseases_info": [...],
  "ai_analysis": { ... }
}
```

---

## 5. Consultation API (`/api/v1`)

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/consult_integrated` | Tư vấn điều trị (KB → AI fallback) |

**Request Body**:
```json
{
  "request_id": "REQ-001",
  "items": [
    { "id": "d1", "name": "Paracetamol" }
  ],
  "diagnoses": [
    { "code": "R51", "name": "Đau đầu", "type": "MAIN" }
  ],
  "symptom": "Nhức đầu, sốt nhẹ"
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "d1",
      "name": "Paracetamol",
      "category": "drug",
      "validity": "valid",
      "role": "Thuốc điều trị chính",
      "explanation": "Internal KB (AI): Found 150 records. Confidence: 95%",
      "source": "INTERNAL_KB_AI"
    }
  ]
}
```

**Source Values**:
- `INTERNAL_KB_TDV`: Từ Knowledge Base (đã có feedback chuyên gia)
- `INTERNAL_KB_AI`: Từ Knowledge Base (AI classification)
- `EXTERNAL_AI`: Từ External AI (OpenAI)
- `ERROR`: Lỗi xử lý

---

## 6. Data Management API (`/api/v1/data`)

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/ingest` | Upload CSV để xây dựng Knowledge Base |

**Request**: `multipart/form-data`
- `file`: CSV file

**Response**:
```json
{
  "status": "processing",
  "batch_id": "uuid-xxx",
  "message": "File received and ETL started."
}
```

---

## 7. Admin API (`/api/v1/admin`)

### 7.1. Drugs Management

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/drugs` | Lấy danh sách thuốc (Admin view) |
| `POST` | `/drugs` | Thêm/Cập nhật thuốc |
| `DELETE` | `/drugs/{sdk}` | Xóa thuốc theo SDK |
| `DELETE` | `/drugs/id/{row_id}` | Xóa thuốc theo ID |

### 7.2. Diseases Management

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/diseases` | Lấy danh sách bệnh |
| `POST` | `/diseases` | Thêm/Cập nhật bệnh |
| `DELETE` | `/diseases/{icd_code}` | Xóa bệnh theo ICD |
| `DELETE` | `/diseases/id/{row_id}` | Xóa bệnh theo ID |

### 7.3. Knowledge Links Management

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/links` | Lấy danh sách liên kết Thuốc-Bệnh |
| `DELETE` | `/links?sdk=X&icd_code=Y` | Xóa liên kết |

---

## Error Handling

Tất cả API trả về format lỗi thống nhất:

```json
{
  "detail": "Error message here"
}
```

| HTTP Code | Ý nghĩa |
|-----------|---------|
| `400` | Bad Request (input không hợp lệ) |
| `404` | Not Found |
| `500` | Internal Server Error |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-19 | 1.0.0 | Initial API documentation |
