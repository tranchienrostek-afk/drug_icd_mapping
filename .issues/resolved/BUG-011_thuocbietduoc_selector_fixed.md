# ISSUE: [BUG-011] - [ThuocBietDuoc Search Selector Fail]
**Status:** Resolved
**Severity:** High
**Affected Component:** Drug Crawler / ThuocBietDuoc Site Config

## 1. Mô tả lỗi (Description)
Docker logs hiển thị ThuocBietDuoc search input không được tìm thấy sau 3 lần retry:
```
[ThuocBietDuoc] Input not found, retrying...
[ThuocBietDuoc] Finding search input (attempt 2)...
[ThuocBietDuoc] Input not found, retrying...
```

## 2. Root Cause
Selector configuration sai - tưởng trang dùng ASP.NET WebForms (`ContentPlaceHolder1`, `txtTenThuoc`) nhưng thực tế dùng modern HTML (`#search-form`, `input[name='key']`).

## 3. Giải pháp
Dùng browser subagent để inspect trang và cập nhật selector đúng.

---
# RESOLUTION NOTE (2026-01-07 16:55)
**Status:** Fixed & Resolved
**Fix Method:** Updated `config.py` with correct selectors from browser inspection:
- Input: `#search-form input[name='key']`
- Action: Changed from `CLICK` to `ENTER`
**Verification:** Docker rebuild successful, container started without errors.
**Report:** [report_2026_01_07_BUG_011.md](file:///C:/Users/Admin/Desktop/drug_icd_mapping/.ai_planning/.implementation_rules/.ai_reports/2026-01/report_2026_01_07_BUG_011.md)
