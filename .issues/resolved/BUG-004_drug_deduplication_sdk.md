# ISSUE: BUG-004 - Lỗi Deduplication khi thuốc không có Số đăng ký (SDK)
**Status:** Resolved
**Severity:** Medium
**Affected Component:** Drug API (`app/api/drugs.py`)

## 1. Mô tả lỗi (Description)
Bộ lọc trùng lặp (Deduplication) dựa trên SDK nhận nhầm các chuỗi placeholder như "Web Result (No SDK)" là SDK hợp lệ. Kết quả là nếu có 2 thuốc cùng loại này (ví dụ Paracetamol và Candesartan cùng không có SDK trong DB), thuốc thứ hai sẽ bị đánh dấu là `is_duplicate: true`.

## 2. Logs & Error Message (QUAN TRỌNG)
```json
 {
  "input_name": "Metformin 500mg",
  "is_duplicate": true,
  "duplicate_of": "Candesartan 16mg"
 }
```
Lỗi do biến `seen_sdk` lưu trữ giá trị 'Web Result (No SDK)'.

## 3. Cách khắc phục (Resolution)
Cập nhật logic trong `identify_drugs`: Loại trừ các chuỗi placeholder ra khỏi quá trình kiểm tra trùng lặp SDK.

```python
if sdk and sdk != 'N/A' and sdk != 'Web Result (No SDK)':
    # ... logic check seen_sdk
```

## 4. Xác nhận (Verification)
Đã xác nhận trên file `verify_results.txt`, hai thuốc khác tên nhưng cùng không có SDK hiện tại đều trả về `is_duplicate: false`.
迫
