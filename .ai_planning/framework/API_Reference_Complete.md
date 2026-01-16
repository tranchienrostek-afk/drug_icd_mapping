# 📋 API Reference - Medical Drug-ICD Mapping System

> **Version**: 1.0.0  
> **Base URL**: `http://localhost:8000/api/v1`  
> **Last Updated**: 2026-01-16

---

## 🔥 Quick Overview

| Group | Endpoints | Description |
|-------|-----------|-------------|
| [Health](#health) | 1 | System health check |
| [Drugs](#drugs-api) | 12 | Drug CRUD, identification, staging workflow |
| [Diseases](#diseases-api) | 1 | Disease lookup by ICD |
| [Consult](#consultation-api) | 1 | Treatment consultation |
| [Analysis](#analysis-api) | 1 | AI-powered treatment analysis |
| [Admin](#admin-api) | 11 | CRUD for drugs, diseases, links |
| [Data Management](#data-management-api) | 1 | CSV ingestion |
| **Total** | **28** | |

---

## Health

### `GET /health`
Check system health and service availability.

**Response:**
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

## Drugs API

Base path: `/drugs`

### 1. `GET /drugs/`
Get paginated list of all drugs.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 10 | Items per page |
| `search` | str | "" | Search keyword |

**Response:**
```json
{
  "data": [
    {
      "rowid": 1,
      "ten_thuoc": "Paracetamol 500mg",
      "so_dang_ky": "VN-12345-67",
      "hoat_chat": "Paracetamol",
      "cong_ty_san_xuat": "Company Name"
    }
  ],
  "total": 65026,
  "page": 1,
  "limit": 10
}
```

---

### 2. `GET /drugs/{row_id}`
Get drug details by row ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| `row_id` | int | Drug row ID |

**Response:** Drug object or `404 Not Found`

---

### 3. `POST /drugs/identify`
Identify drugs from a list of names.

**Request Body:**
```json
{
  "drugs": [
    "Paracetamol 500mg",
    "Amoxicillin 250mg"
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "input": "Paracetamol 500mg",
      "matched_drug": {...},
      "status": "found",
      "confidence": 0.95
    }
  ]
}
```

---

### 4. `POST /drugs/confirm`
Save a verified drug to the database.

**Request Body:**
```json
{
  "ten_thuoc": "Panadol Extra",
  "so_dang_ky": "VN-12345-67",
  "hoat_chat": "Paracetamol, Caffeine",
  "chi_dinh": "Giảm đau, hạ sốt",
  "cong_ty_san_xuat": "GSK",
  "tu_dong_nghia": "Panadol đỏ",
  "modified_by": "admin"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Drug saved successfully",
  "id": 123
}
```

---

### 5. `POST /drugs/knowledge/link`
Create a drug-disease link in knowledge base.

**Request Body:**
```json
{
  "drug_name": "Panadol Extra",
  "sdk": "VN-12345-67",
  "disease_name": "Đau đầu",
  "icd_code": "R51",
  "treatment_note": "Thuốc đầu tay cho đau đầu nhẹ",
  "is_verified": 1,
  "coverage_type": "Thuốc điều trị",
  "created_by": "admin"
}
```

**Response:**
```json
{
  "status": "created",
  "message": "Link created: VN-12345-67 <-> R51",
  "id": 456
}
```

---

### 6. `GET /drugs/admin/staging`
Get list of pending drugs in staging.

**Response:**
```json
[
  {
    "id": 1,
    "ten_thuoc": "New Drug",
    "so_dang_ky": "VN-99999-00",
    "status": "pending",
    "conflict_type": "sdk",
    "created_at": "2026-01-16 10:00:00"
  }
]
```

---

### 7. `POST /drugs/admin/approve/{staging_id}`
Approve a drug from staging to main table.

| Parameter | Type | Description |
|-----------|------|-------------|
| `staging_id` | int | Staging record ID |
| `user` | str | Approver username (query param) |

**Response:**
```json
{
  "status": "success",
  "message": "Drug approved"
}
```

---

### 8. `POST /drugs/admin/reject/{staging_id}`
Reject a drug from staging.

| Parameter | Type | Description |
|-----------|------|-------------|
| `staging_id` | int | Staging record ID |

---

### 9. `PUT /drugs/admin/staging/{staging_id}`
Update drug information in staging.

**Request Body:**
```json
{
  "ten_thuoc": "Updated Name",
  "hoat_chat": "Updated Ingredient",
  "modified_by": "admin"
}
```

---

### 10. `POST /drugs/admin/staging/clear`
Clear all pending staging items (move to history).

---

### 11. `POST /drugs/agent-search`
Use AI agent (browser) to search for drug information.

**Request Body:**
```json
{
  "drugs": ["Thuốc mới XYZ"]
}
```

**Response:**
```json
{
  "results": [
    {
      "drug_name": "Thuốc mới XYZ",
      "status": "found",
      "data": {...}
    }
  ]
}
```

---

## Diseases API

Base path: `/diseases`

### 12. `POST /diseases/lookup`
Lookup diseases by name and ICD code.

**Request Body:**
```json
{
  "diagnosis": [
    {"name": "Đau đầu", "icd10": "R51"},
    {"name": "Tăng huyết áp", "icd10": "I10"}
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "input_diagnosis": "Đau đầu",
      "icd10_input": "R51",
      "official_name": "Đau đầu",
      "icd_code": "R51",
      "chapter": "Triệu chứng tổng quát",
      "source": "KnowledgeBase"
    }
  ]
}
```

---

## Consultation API

Base path: `/`

### 13. `POST /consult_integrated`
Hybrid consultation: Internal KB + AI fallback.

**Request Body:**
```json
{
  "request_id": "req-001",
  "items": [
    {"id": "drug1", "name": "Paracetamol 500mg"},
    {"id": "drug2", "name": "Amoxicillin 500mg"}
  ],
  "diagnoses": [
    {"code": "J06.9", "name": "Nhiễm trùng hô hấp cấp", "type": "MAIN"},
    {"code": "R51", "name": "Đau đầu", "type": "SECONDARY"}
  ],
  "symptom": "Sốt, đau đầu"
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "drug1",
      "name": "Paracetamol 500mg",
      "category": "drug",
      "validity": "valid",
      "role": "Điều trị chính",
      "explanation": "Internal KB: Found 90 records. Confidence: 92%",
      "source": "INTERNAL_KB"
    }
  ]
}
```

---

## Analysis API

Base path: `/analysis`

### 14. `POST /analysis/treatment-analysis`
Full treatment analysis combining drugs, diseases, and AI.

**Request Body:**
```json
{
  "drugs": [
    "Candesartan 16mg",
    "Paracetamol 500mg"
  ],
  "diagnosis": [
    {"name": "Tăng huyết áp", "icd10": "I10"},
    {"name": "Đau đầu", "icd10": "R51"}
  ]
}
```

**Response:**
```json
{
  "drugs_info": [...],
  "diseases_info": [...],
  "ai_analysis": {
    "summary": "Phác đồ phù hợp...",
    "recommendations": [...]
  }
}
```

---

## Admin API

Base path: `/admin`

### 15. `GET /admin/drugs`
Get drugs list (admin view).

| Parameter | Type | Default |
|-----------|------|---------|
| `page` | int | 1 |
| `limit` | int | 20 |
| `search` | str | "" |

---

### 16. `POST /admin/drugs`
Save new drug via admin.

**Request Body:** Same as `/drugs/confirm`

---

### 17. `DELETE /admin/drugs/{sdk}`
Delete drug by registration number (SDK).

---

### 18. `DELETE /admin/drugs/id/{row_id}`
Delete drug by row ID.

---

### 19. `GET /admin/diseases`
Get diseases list.

| Parameter | Type | Default |
|-----------|------|---------|
| `page` | int | 1 |
| `limit` | int | 20 |
| `search` | str | "" |

---

### 20. `POST /admin/diseases`
Save new disease.

**Request Body:**
```json
{
  "icd_code": "R51",
  "disease_name": "Đau đầu",
  "chapter_name": "Triệu chứng tổng quát"
}
```

---

### 21. `DELETE /admin/diseases/{icd_code}`
Delete disease by ICD code.

---

### 22. `DELETE /admin/diseases/id/{row_id}`
Delete disease by row ID.

---

### 23. `GET /admin/links`
Get drug-disease links from knowledge base.

| Parameter | Type | Default |
|-----------|------|---------|
| `page` | int | 1 |
| `limit` | int | 20 |
| `search` | str | "" |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "drug_name": "paracetamol",
      "icd_code": "R51",
      "disease_name": "đau đầu",
      "phan_loai": "valid",
      "frequency": 125
    }
  ],
  "total": 5000,
  "page": 1,
  "limit": 20
}
```

---

### 24. `DELETE /admin/links`
Delete a drug-disease link.

| Parameter | Type | Description |
|-----------|------|-------------|
| `sdk` | str | Drug SDK |
| `icd_code` | str | Disease ICD code |

---

## Data Management API

Base path: `/data`

### 25. `POST /data/ingest`
Ingest CSV file for knowledge base building.

**Request:** `multipart/form-data`
- `file`: CSV file

**CSV Format:**
```csv
drug_name,disease_name,icd_code,phan_loai
Paracetamol,Đau đầu,R51,valid
Amoxicillin,Viêm họng,J06.9,valid
```

**Response:**
```json
{
  "status": "processing",
  "batch_id": "abc123-uuid",
  "message": "File received and ETL started."
}
```

> ⚠️ **Note**: ETL runs in background. Check `knowledge_base` table for results.

---

## Error Responses

All APIs return standard error format:

```json
{
  "detail": "Error message here"
}
```

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Invalid input |
| `404` | Not Found - Resource not found |
| `405` | Method Not Allowed |
| `422` | Unprocessable Entity - Validation error |
| `500` | Internal Server Error |

---

## Authentication

> 🔒 **Note**: Current version does not implement authentication. Planned for v2.0.

---

## Rate Limiting

No rate limiting implemented in current version.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-16 | Initial release with 25+ endpoints |
