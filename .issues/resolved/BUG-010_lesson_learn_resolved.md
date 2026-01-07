# ISSUE: [BUG-010] - [Lesson Learn]
**Status:** Open
**Severity:** High
**Affected Component:**Drug Search, Drug Crawler
**created:** 2026-01-07
**created by:** Trần Văn Chiến

## 1. Mô tả lỗi (Description)
vì sao file C:\Users\Admin\Desktop\drug_icd_mapping\scripts\2026_01_07_15_35_crapper_data_drugs.py lấy dữ liệu ổn định và rất ngon từ trang web thuốc biệt dược
Mà sao ứng dụng search cũng lấy dữ liệu từ trang web đó lại không ổn định như thế
Bạn có thể học hỏi được điều gì không chứ thực sự các thuật toán search vẫn lỗi

## 2. Logs & Error Message (QUAN TRỌNG)
{
  "results": [
    {
      "input_name": "Ludox - 200mg",
      "official_name": null,
      "sdk": null,
      "active_ingredient": null,
      "usage": "N/A",
      "source": "Web",
      "confidence": 0.8,
      "source_urls": [],
      "is_duplicate": false
    },
    {
      "input_name": "Althax - 120mg",
      "official_name": null,
      "sdk": null,
      "active_ingredient": null,
      "usage": "N/A",
      "source": "Web",
      "confidence": 0.8,
      "source_urls": [],
      "is_duplicate": false
    },
    {
      "input_name": "Hightamine",
      "official_name": null,
      "sdk": null,
      "active_ingredient": null,
      "usage": "N/A",
      "source": "Web",
      "confidence": 0.8,
      "source_urls": [],
      "is_duplicate": false
    }
  ]
}

---
# RESOLUTION NOTE (2026-01-07 16:05)
**Status:** Analyzed & Fixed
**Lessons Applied to `core_drug.py` v4:**
1. Resource blocking (faster loading)
2. 60s timeout (more patient)
3. 3-retry logic (more resilient)
4. `ignore_https_errors=True` (more robust)
5. Longer wait for dynamic content (3s)

**Report:** [report_2026_01_07_BUG_010.md](file:///C:/Users/Admin/Desktop/drug_icd_mapping/.ai_planning/.implementation_rules/.ai_reports/2026-01/report_2026_01_07_BUG_010.md)