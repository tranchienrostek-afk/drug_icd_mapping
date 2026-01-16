# 📊 API Documentation: `POST /data/ingest`

> **Endpoint**: `POST /api/v1/data/ingest`  
> **Version**: 2.0.0  
> **Last Updated**: 2026-01-16

---

## 🎯 Tổng Quan

API này cho phép khách hàng upload file CSV chứa dữ liệu thuốc-bệnh để xây dựng **Knowledge Base**.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Client    │────▶│  API Layer  │────▶│ ETL Service │────▶│ Knowledge DB │
│  (CSV File) │     │  Validation │     │ (Background)│     │  (SQLite)    │
└─────────────┘     └─────────────┘     └─────────────┘     └──────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  raw_logs   │
                    │  (Backup)   │
                    └─────────────┘
```

---

## 📁 Files Liên Quan

| File | Vai trò |
|------|---------|
| `app/api/data_management.py` | API Controller |
| `app/service/etl_service.py` | ETL Logic - parse, transform, load |
| `app/services.py` | `DrugDbEngine.log_raw_data()` |
| `app/database/core.py` | Schema: `raw_logs`, `knowledge_base` |
| `app/core/utils.py` | `normalize_drug_name()`, `normalize_text()` |

---

## 📋 Định Dạng Đầu Vào (CSV)

### Cấu Trúc File CSV

```csv
Tên thuốc,Mã ICD (Chính),Bệnh phụ,Chẩn đoán ra viện,Phân loại,Feedback,Lý do kê đơn,Cách dùng,SL
Paracetamol 500mg,J00 - Viêm mũi họng cấp,B97.4 - Vi rút hợp bào,Sốt cao kèm đau đầu,"drug, main","drug","Hạ sốt giảm đau",Uống 2 viên/lần,20
```

### Chi Tiết Xử Lý Từng Cột

| Cột CSV | Bắt buộc | Xử lý | Cột DB đích |
|---------|----------|-------|-------------|
| **Tên thuốc** | ✅ Có | Lưu gốc + normalize | `drug_name`, `drug_name_norm` |
| **Mã ICD (Chính)** | ✅ Có | Bóc tách mã + tên | `disease_icd`, `disease_name`, `disease_name_norm`, `disease_ref_id` |
| **Bệnh phụ** | ❌ Không | Bóc tách mã + tên | `secondary_disease_icd`, `secondary_disease_name`, `secondary_disease_name_norm`, `secondary_disease_ref_id` |
| **Chẩn đoán ra viện** | ❌ Không | Giữ nguyên | `symptom` |
| **Phân loại** | ❌ Không | Merge với Feedback | `treatment_type` (phần AI) |
| **Feedback** | ❌ Không | Merge với Phân loại | `treatment_type` (phần TDV) |
| **Lý do kê đơn** | ❌ Không | Giữ nguyên | `prescription_reason` |
| **Cách dùng** | - | ⏭️ Bỏ qua | - |
| **SL** | - | ⏭️ Bỏ qua | - |

---

## 🔄 Logic Xử Lý Chi Tiết

### 1. Xử Lý Cột "Tên thuốc"

**Input CSV:**
```
Tên thuốc: "Paracetamol 500mg Tablets"
```

**Output DB:**
```python
drug_name = "Paracetamol 500mg Tablets"  # Giữ nguyên gốc
drug_name_norm = "paracetamol 500mg tablets"  # Lowercase, bỏ dấu
```

---

### 2. Xử Lý Cột "Mã ICD (Chính)"

**Input CSV:**
```
Mã ICD (Chính): "J00 - Viêm mũi họng cấp [cảm thường]"
```

**Bóc tách:**
```python
# Parse pattern: "CODE - Name"
match = re.match(r'^([A-Z]\d+(?:\.\d+)?)\s*-\s*(.+)$', value)

disease_icd = "j00"  # Lowercase
disease_name = "Viêm mũi họng cấp [cảm thường]"  # Gốc
disease_name_norm = "viêm mũi họng cấp cảm thường"  # Normalize
disease_ref_id = lookup_disease_id("j00")  # FK to diseases table
```

---

### 3. Xử Lý Cột "Bệnh phụ"

**Input CSV:**
```
Bệnh phụ: "B97.4 - Vi rút hợp bào đường hô hấp"
```

**Bóc tách tương tự:**
```python
secondary_disease_icd = "b97.4"
secondary_disease_name = "Vi rút hợp bào đường hô hấp"
secondary_disease_name_norm = "vi rut hop bao duong ho hap"
secondary_disease_ref_id = lookup_disease_id("b97.4")
```

---

### 4. Xử Lý Cột "Phân loại" & "Feedback"

Hệ thống sẽ lưu trữ vào 2 cột riêng biệt:

**Input CSV:**
```
Phân loại: "drug, main"
Feedback: "drug"
```

**Output DB:**
```python
treatment_type = "drug, main"  # Cột Phân loại (AI)
tdv_feedback = "drug"          # Cột Feedback (TDV)
```

> **Note (v2.1)**: Trước đây (v2.0) merged thành 1 string, nay tách ra để query linh hoạt hơn.

---

### 5. Xử Lý Cột "Chẩn đoán ra viện" → `symptom`

**Input CSV:**
```
Chẩn đoán ra viện: "Sốt cao kèm đau đầu, mệt mỏi"
```

**Output DB:**
```python
symptom = "Sốt cao kèm đau đầu, mệt mỏi"  # Giữ nguyên
```
---

### 6. Mapping Bảng

| Cột CSV | Cột DB | Mô tả |
|---------|--------|-------|
| Phân loại | `treatment_type` | AI Classification |
| Feedback | `tdv_feedback` | Chuyên gia thẩm định |

---

## 🗃️ Schema Database Mới (v2.1)

### Bảng `knowledge_base`

```sql
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Drug Info
    drug_name TEXT,
    drug_name_norm TEXT,
    drug_ref_id INTEGER,
    
    -- Primary Disease
    disease_icd TEXT,
    disease_name TEXT,
    disease_name_norm TEXT,
    disease_ref_id INTEGER,
    
    -- Secondary Disease
    secondary_disease_icd TEXT,
    secondary_disease_name TEXT,
    secondary_disease_name_norm TEXT,
    secondary_disease_ref_id INTEGER,
    
    -- Classification
    treatment_type TEXT,                -- AI Classification (Phân loại)
    tdv_feedback TEXT,                  -- TDV Feedback
    
    -- Additional Info
    symptom TEXT,
    prescription_reason TEXT,
    
    -- Metadata
    frequency INTEGER DEFAULT 1,
    confidence_score REAL DEFAULT 0.0,
    batch_id TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 ETL Code Flow

```python
def process_raw_log(batch_id: str, text_content: str):
    for row in csv_rows:
        # 1. Parse Drug
        drug_name = row.get('Tên thuốc', '').strip()
        drug_name_norm = normalize_text(drug_name)
        
        # 2. Parse Primary Disease
        disease_icd, disease_name = parse_icd_field(row.get('Mã ICD (Chính)', ''))
        disease_name_norm = normalize_text(disease_name)
        disease_ref_id = lookup_disease_id(disease_icd)
        
        # 3. Parse Secondary Disease
        sec_icd, sec_name = parse_icd_field(row.get('Bệnh phụ', ''))
        sec_name_norm = normalize_text(sec_name)
        sec_ref_id = lookup_disease_id(sec_icd)
        
        # 4. Merge Classification
        phan_loai = row.get('Phân loại', '').strip()
        feedback = row.get('Feedback', '').strip()
        treatment_type = f"AI: {{{phan_loai}}}, TDV: {{{feedback}}}"
        
        # 5. Other fields
        symptom = row.get('Chẩn đoán ra viện', '').strip()
        prescription_reason = row.get('Lý do kê đơn', '').strip()
        
        # 6. Insert to DB
        cursor.execute("""
            INSERT INTO knowledge_base 
            (drug_name, drug_name_norm, disease_icd, disease_name, disease_name_norm, 
             disease_ref_id, secondary_disease_icd, secondary_disease_name, 
             secondary_disease_name_norm, secondary_disease_ref_id,
             treatment_type, symptom, prescription_reason, batch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (...))

def parse_icd_field(value: str) -> tuple:
    """Parse 'J00 - Viêm mũi họng' into ('j00', 'Viêm mũi họng')"""
    if not value:
        return ('', '')
    match = re.match(r'^([A-Z]\d+(?:\.\d+)?)\s*-\s*(.+)$', value.strip(), re.IGNORECASE)
    if match:
        return (match.group(1).lower(), match.group(2).strip())
    return ('', value.strip())
```

---

## 📤 Response Format

### Success (HTTP 200)
```json
{
    "status": "processing",
    "batch_id": "a1b2c3d4-...",
    "message": "File received and ETL started."
}
```

### Errors
| Status | Detail |
|--------|--------|
| 400 | "Only CSV files are allowed." |
| 500 | Server/Database error |

---

## 🧪 Test Cases

```bash
pytest test_comprehensive_api.py::TestDataManagement -v
```

---

## 📊 Ví Dụ Mapping Hoàn Chỉnh

**CSV Input:**
```csv
Tên thuốc,Mã ICD (Chính),Bệnh phụ,Chẩn đoán ra viện,Phân loại,Feedback,Lý do kê đơn
Paracetamol 500mg,J00 - Viêm mũi họng cấp,B97.4 - Vi rút hợp bào,Sốt cao đau đầu,"drug, main","drug","Hạ sốt"
```

**Database Record:**
```json
{
    "drug_name": "Paracetamol 500mg",
    "drug_name_norm": "paracetamol 500mg",
    "disease_icd": "j00",
    "disease_name": "Viêm mũi họng cấp",
    "disease_name_norm": "viem mui hong cap",
    "disease_ref_id": 123,
    "secondary_disease_icd": "b97.4",
    "secondary_disease_name": "Vi rút hợp bào",
    "secondary_disease_name_norm": "vi rut hop bao",
    "secondary_disease_ref_id": 456,
    "treatment_type": "AI: {drug, main}, TDV: {drug}",
    "symptom": "Sốt cao đau đầu",
    "prescription_reason": "Hạ sốt",
    "frequency": 1,
    "batch_id": "abc-123..."
}
```

---

## 📚 Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-16 | 2.0.0 | Thêm cột: drug_name gốc, secondary disease, symptom, prescription_reason. Merge Phân loại + Feedback. |
| 2026-01-16 | 1.0.0 | Initial documentation |
