# API Specifications - Diseases (`/diseases`)

## Base URL
```
http://localhost:8000/api/v1
```

---

## 1. Diseases API (`/diseases`)

### 1.1 POST `/diseases/lookup`
**Mô tả**: Tra cứu thông tin bệnh ICD-10.

**Request:**
```json
{
  "diagnosis": [
    {"name": "Đau đầu", "icd10": "R51"}
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
      "official_name": "Headache",
      "icd_code": "R51",
      "chapter": "Chapter XVIII",
      "source": "Database"
    }
  ]
}
```

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
