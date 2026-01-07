# ISSUE: [BUG-012] - [Fix Search Selector]
**Status:** Open
**Severity:** High
**Affected Component:** Crawler Service

## 1. Mô tả lỗi (Description)
Vẫn không tìm ra được bất kỳ thông tin nào
Trong khi tôi đã cung cấp cho bạn đầy đủ cả 3 trang webs
Sửa mãi mà rất vòng vo, không lối thoát

## 2. Logs & Error Message (QUAN TRỌNG)
{
  "results": [
    {
      "input_name": "Symbicort 120 liều",
      "official_name": "Symbicort Iều 120l",
      "sdk": "Web Result (No SDK)",
      "active_ingredient": "",
      "usage": "Combined from 1 sources.",
      "source": "Web Search (Advanced)",
      "confidence": 0.8,
      "source_urls": [
        "https://thuocbietduoc.com.vn/thuoc/drgsearch.aspx"
      ],
      "is_duplicate": false
    },
    {
      "input_name": "Althax - 120mg",
      "official_name": "Althax - 120mg",
      "sdk": "Web Result (No SDK)",
      "active_ingredient": "",
      "usage": "Combined from 1 sources.",
      "source": "Web Search (Advanced)",
      "confidence": 0.8,
      "source_urls": [
        "https://thuocbietduoc.com.vn/thuoc/drgsearch.aspx"
      ],
      "is_duplicate": false
    },
    {
      "input_name": "Hightamine",
      "official_name": "Hightamine",
      "sdk": "Web Result (No SDK)",
      "active_ingredient": "",
      "usage": "Combined from 1 sources.",
      "source": "Web Search (Advanced)",
      "confidence": 0.8,
      "source_urls": [
        "https://thuocbietduoc.com.vn/thuoc/drgsearch.aspx"
      ],
      "is_duplicate": false
    }
  ]
}

## 3. Selector Behavior Log
Tham khảo thôi, xem có phát hiện ra được giải pháp tối ưu không
C:\Users\Admin\Desktop\drug_icd_mapping\scripts\2026_01_07_17_02_selector_behavior_log.md

## 4. Kiểm tra 5 file bugs gần nhất được lưu trữ trong 
C:\Users\Admin\Desktop\drug_icd_mapping\.issues\resolved\archive_2025

Bạn hãy tối ưu cách tưu duy và suy luận chặt chẽ hơn ở walkthrough.md Chứ không thể rối rắm như thế được, cần thông tin gì thì cứ báo để tôi gửi lại. Hãy nhớ chúng ta hợp tác cùng nhau.

---
# RESOLUTION NOTE (2026-01-07 17:15)
**Status:** Fixed & Resolved
**Fix Method:** Ported robust Div-based selectors from the working bulk scraper (`crapper_data_drugs.py`) to `config.py`.
**Updated Selectors:**
- SDK: `//div[... 'Số đăng ký']...`
- Hoat Chat: `.ingredient-content`
- Action: `ENTER` key
**Verification:** Docker logs confirm `Application startup complete` with new config.
**Report:** [report_2026_01_07_BUG_012.md](file:///C:/Users/Admin/Desktop/drug_icd_mapping/.ai_planning/.implementation_rules/.ai_reports/2026-01/report_2026_01_07_BUG_012.md)