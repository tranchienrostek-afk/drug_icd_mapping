# Domain: ETL Pipeline

Quy trình xử lý dữ liệu (Extract - Transform - Load) cho việc xây dựng Knowledge Base từ CSV logs.

---

## 1. Tổng quan Kiến trúc

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌───────────────┐
│  CSV File   │────▶│  Ingest API │────▶│  ETL Service    │────▶│ knowledge_base│
│  (Upload)   │     │  /data/ing  │     │  (Background)   │     │    (SQLite)   │
└─────────────┘     └─────────────┘     └─────────────────┘     └───────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  raw_logs   │
                    │  (Backup)   │
                    └─────────────┘
```

---

## 2. API Entry Point

**Endpoint**: `POST /api/v1/data/ingest`

**Input**: CSV file (multipart/form-data)

**Process**:
1. Validate file extension (.csv)
2. Generate `batch_id` (UUID)
3. Log raw content → `raw_logs` table
4. Trigger Background Task → `process_raw_log()`
5. Return immediately with `batch_id`

---

## 3. CSV Format Specification

### 3.1. Required Columns

| Cột CSV | Bắt buộc | Format | Ví dụ |
|---------|----------|--------|-------|
| `Tên thuốc` | ✅ | Text | Paracetamol 500mg |
| `Mã ICD (Chính)` | ✅ | `CODE - Tên bệnh` | J00 - Viêm mũi họng cấp |

### 3.2. Optional Columns

| Cột CSV | Format | Map to DB |
|---------|--------|-----------|
| `Bệnh phụ` | `CODE - Tên bệnh` | `secondary_disease_*` |
| `Chẩn đoán ra viện` | Text tự do | `symptom` |
| `Phân loại` | Comma-separated tags | `treatment_type` |
| `Feedback` | Comma-separated tags | `tdv_feedback` |
| `Lý do kê đơn` | Text | `prescription_reason` |
| `Cách dùng` | ⏭️ Ignored | - |
| `SL` | ⏭️ Ignored | - |

### 3.3. Sample CSV

```csv
Tên thuốc,Mã ICD (Chính),Bệnh phụ,Phân loại,Feedback,Chẩn đoán ra viện
Paracetamol 500mg,J00 - Viêm mũi họng cấp,B97.4 - Vi rút hợp bào,"drug, main",drug,Sốt cao kèm ho
Amoxicillin 250mg,J02 - Viêm họng cấp,,"drug, support",,Viêm họng
```

---

## 4. ETL Processing (`process_raw_log`)

**Location**: `app/service/etl_service.py`

### 4.1. Flow Chart

```
┌──────────────────┐
│ Parse CSV        │
│ (DictReader)     │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ For Each Row:    │
│ ├─ Validate      │
│ ├─ Normalize     │
│ └─ Lookup Refs   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Upsert to        │
│ knowledge_base   │
│ (Insert/Update)  │
└──────────────────┘
```

### 4.2. Transform Rules

#### Drug Name
```python
drug_name_norm = normalize_text(drug_name)  # lowercase, remove accents
```

#### ICD Field Parsing
```python
# Input: "J00 - Viêm mũi họng cấp"
# Output: ("j00", "Viêm mũi họng cấp")

def parse_icd_field(value: str) -> tuple:
    match = re.match(r'^([A-Z]\d+(?:\.\d+)?)\s*-\s*(.+)$', value, re.IGNORECASE)
    if match:
        return (match.group(1).lower(), match.group(2).strip())
    return ('', value)
```

#### Disease Reference Lookup
```python
def lookup_disease_ref_id(cursor, icd_code: str) -> int:
    cursor.execute("SELECT id FROM diseases WHERE LOWER(icd_code) = ?", (icd_code,))
    row = cursor.fetchone()
    return row['id'] if row else None
```

### 4.3. Upsert Logic

```sql
-- Check existing
SELECT id, frequency FROM knowledge_base 
WHERE drug_name_norm = ? AND disease_icd = ?

-- If EXISTS → UPDATE
UPDATE knowledge_base 
SET frequency = frequency + 1,
    treatment_type = COALESCE(?, treatment_type),
    tdv_feedback = COALESCE(?, tdv_feedback),
    last_updated = CURRENT_TIMESTAMP
WHERE id = ?

-- If NOT EXISTS → INSERT
INSERT INTO knowledge_base 
(drug_name, drug_name_norm, disease_icd, disease_name, ..., frequency)
VALUES (?, ?, ?, ?, ..., 1)
```

---

## 5. Database Schema Migration

ETL Service tự động thêm các cột mới nếu chưa tồn tại:

```python
def _ensure_kb_columns(cursor):
    new_columns = [
        ("drug_name", "TEXT"),
        ("secondary_disease_icd", "TEXT"),
        ("secondary_disease_name", "TEXT"),
        ("symptom", "TEXT"),
        ("prescription_reason", "TEXT"),
        ("batch_id", "TEXT"),
        ("tdv_feedback", "TEXT"),
    ]
    for col_name, col_type in new_columns:
        cursor.execute(f"ALTER TABLE knowledge_base ADD COLUMN {col_name} {col_type}")
```

---

## 6. Error Handling

| Error Type | Handling |
|------------|----------|
| Missing required field | Skip row, log error, continue |
| DB connection error | Raise exception, stop batch |
| Invalid ICD format | Store raw value in `disease_name` |

**Logging**:
```python
logger.info(f"[ETL] Batch {batch_id} complete: {inserted} inserted, {updated} updated, {errors} errors")
```

---

## 7. Legacy Support

Class `EtlService` được giữ lại để backward compatibility với các script cũ:

| Method | Mô tả |
|--------|-------|
| `load_csv(file_path)` | Load CSV an toàn |
| `clean_and_deduplicate(df)` | Xử lý trùng lặp theo `so_dang_ky` |
| `extract_info_from_description(text)` | Trích xuất chỉ định từ mô tả |
| `process_for_import(df)` | Convert DataFrame → List[Dict] |

---

## 8. Monitoring & Audit

### Raw Logs Table
Mọi dữ liệu upload đều được lưu vào `raw_logs` trước khi xử lý:

```sql
INSERT INTO raw_logs (batch_id, raw_content, source_ip, created_at)
VALUES (?, ?, 'API_UPLOAD', CURRENT_TIMESTAMP)
```

### Batch Tracking
Mỗi record trong `knowledge_base` có `batch_id` để trace nguồn gốc.

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-19 | 2.0.0 | Documented full ETL pipeline with secondary disease support |
| 2026-01-16 | 1.0.0 | Initial ETL implementation |
