# ISSUE: BUG-003 - Dữ liệu bệnh lý (Diseases) bị trả về null
**Status:** Resolved
**Severity:** High
**Affected Component:** Disease API (`app/api/diseases.py`)

## 1. Mô tả lỗi (Description)
Khi gọi API `/api/v1/analysis/treatment-analysis`, tất cả thông tin trong mảng `diseases_info` (ngoại trừ tên input) đều trả về `null` mặc dù mã ICD-10 đã được cung cấp chính xác.

## 2. Logs & Error Message (QUAN TRỌNG)
Dữ liệu trả về từ `DiseaseDbEngine.search` vốn đã bao bọc trong một dictionary `data`, nhưng code gọi lại truy cập trực tiếp vào dictionary wrapper.

```python
# Lỗi logic
official_name = info.get('disease_name') # Trả về None vì key nằm trong info['data']
```

## 3. Cách khắc phục (Resolution)
Thay đổi cách truy cập dữ liệu từ kết quả tìm kiếm database:
```python
# Sửa đổi trong app/api/diseases.py
disease_data = info.get('data', {})
official_name = disease_data.get('disease_name')
```

## 4. Xác nhận (Verification)
Đã chạy `test_treatment_analysis.py`, kết quả trả về đầy đủ `official_name`, `icd_code` và `chapter_name`.
