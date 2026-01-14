# API Specifications - Drugs (`/drugs`)

## Base URL
```
http://localhost:8000/api/v1
```

---

## 1. Drugs API (`/drugs`)

### 1.1 POST `/drugs/identify`
**Mô tả**: Xác định thông tin thuốc từ danh sách tên/SDK.

**Request:**
```json
{
  "drugs": ["Paracetamol 500mg", "Amoxicillin 250mg"]
}
```

**Response:**
```json
{
  "results": [
    {
      "input_name": "Paracetamol 500mg",
      "db_match": true,
      "official_name": "Paracetamol",
      "sdk": "VN-12345-22",
      "active_ingredient": "Paracetamol",
      "source": "Database"
    }
  ]
}
```

---

### 1.2 POST `/drugs/agent-search`
**Mô tả**: Kích hoạt AI Agent (Browser) để tìm kiếm thuốc trên web. Tối đa 5 rounds/thuốc.

**Request:**
```json
{
  "drugs": ["Ludox - 200mg", "Berodual 200 liều"]
}
```

**Response:**
```json
{
  "results": [
    {
      "status": "success",
      "data": {
        "input_name": "Ludox - 200mg",
        "official_name": "Ludox",
        "sdk": "VN-5145-16",
        "active_ingredient": "Amisulpride",
        "usage": "Điều trị tâm thần phân liệt",
        "confidence": 0.9,
        "source_url": "https://trungtamthuoc.com/thuoc/ludox"
      },
      "rounds": 2,
      "steps": ["Round 1: navigate", "Round 2: answer"]
    }
  ]
}
```

---

### 1.3 GET `/drugs/all`
**Mô tả**: Lấy danh sách thuốc với phân trang.

**Query Parameters:**
| Param | Type | Default | Mô tả |
|-------|------|---------|-------|
| page | int | 1 | Số trang |
| limit | int | 10 | Số item/trang |
| search | string | "" | Tìm kiếm theo tên |

**Response:**
```json
{
  "data": [
    {"id": 1, "drug_name": "Paracetamol", "sdk": "VN-12345-22"}
  ],
  "total": 100,
  "page": 1
}
```

---

### 1.4 GET `/drugs/{row_id}`
**Mô tả**: Lấy chi tiết thuốc theo ID.

---

### 1.5 POST `/drugs/confirm`
**Mô tả**: Lưu thông tin thuốc đã kiểm chứng vào DB.

**Request:**
```json
{
  "drug_name": "Paracetamol",
  "sdk": "VN-12345-22",
  "active_ingredient": "Paracetamol",
  "classification": "Giảm đau",
  "note": "OTC"
}
```

---

### 1.6 POST `/drugs/link-knowledge`
**Mô tả**: Móc nối kiến thức Thuốc (SDK) - Bệnh (ICD).

**Request:**
```json
{
  "drug_name": "Paracetamol",
  "sdk": "VN-12345-22",
  "disease_name": "Đau đầu",
  "icd_code": "R51"
}
```

---

### 1.7 Staging APIs (Thuốc chờ duyệt)

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/drugs/staging` | GET | Lấy danh sách chờ duyệt |
| `/drugs/staging/{id}/approve` | POST | Duyệt thuốc |
| `/drugs/staging/{id}/reject` | POST | Từ chối thuốc |
| `/drugs/staging/{id}` | PUT | Cập nhật thông tin |
| `/drugs/staging/clear` | DELETE | Xóa toàn bộ staging |

---

## 2. Error Responses

**Chuẩn Error Format:**
```json
{
  "detail": "Error message"
}
```

**HTTP Status Codes:**
| Code | Mô tả |
|------|-------|
| 200 | Thành công |
| 400 | Bad Request - Thiếu tham số |
| 404 | Not Found - Không tìm thấy |
| 500 | Server Error |

---

## 3. Authentication (Future)

> [!NOTE]
> Hiện tại chưa yêu cầu authentication. Sẽ implement trong version 2.

---

*Last Updated: 2026-01-14*
