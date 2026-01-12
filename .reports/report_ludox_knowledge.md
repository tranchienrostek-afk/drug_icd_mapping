# Report: Knowledge Script Test (TrungTamThuoc Extract)
**Date**: 2026-01-09
**Script**: `knowledge for agent/trungtamthuoc_extract.py`
**Target**: `https://trungtamthuoc.com/ludox-200mg`

## 1. Results
The script successfully extracted the following data:

- **URL**: `https://trungtamthuoc.com/ludox-200mg`
- **Số đăng ký**: `VN-17269-13` (Successfully extracted)
- **Hoạt chất**: `Cefpodoxim: 200mg`
- **Dạng bào chế**: `Viên nén bao phim`
- **Quy cách**: `Hộp 2 vỉ x 10 viên`
- **Công ty SX**: `Công ty Cổ phần xuất nhập khẩu Y tế Domesco`
- **Error**: `None`

## 2. Comparison with Previous Tests

| Metric | Test 1: Log Analysis | Test 2: `test_ludox_ttt.py` | Test 3: Knowledge Script |
| :--- | :--- | :--- | :--- |
| **Status** | 0 Results (Not Found) | FOUND (Link Only) | **FOUND & EXTRACTED** |
| **SDK** | N/A | `N/A` (Missed) | `VN-17269-13` (Captured) |
| **Logic** | Aggressive Blocking (CSS Blocked) | General Scraper Logic (Generic Selectors) | **Specialized Logic** (Table-based XPath) |

## 3. Conclusion
- **Root Cause of Missing SDK in Test 2**: The generic crawler in `core_drug.py` uses a generic selector:
  `//tr[td[contains(text(), 'Số đăng ký')]]/td[2]`
  The **Knowledge Script** uses:
  `//tr[td[contains(normalize-space(), 'Số đăng ký')]]/td[last()]`
  The `normalize-space()` and `td[last()]` handling in the knowledge script makes it more robust against whitespace or column variations.

- **Effectiveness**: The `trungtamthuoc_extract.py` in the `knowledge for agent` folder is highly effective and contains "Winning Logic" that should be backported to the main `core_drug.py` configuration.

## 4. Final Recommendation
Update the main `app/service/crawler/config.py` to use the more robust XPath selectors found in `trungtamthuoc_extract.py`.
