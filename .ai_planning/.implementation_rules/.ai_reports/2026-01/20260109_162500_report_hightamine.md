# REPORT: Hightamine Data Availability & API Verification
**Date:** 2026-01-09 16:25
**Subject:** Verification of "Hightamine" extraction on TrungTamThuoc.com

## 1. Test Execution
- **Script:** `tests/result_tests/test_hightamine_manual.py`
- **Target Site:** https://trungtamthuoc.com/
- **Keyword:** "Hightamine"
- **Result Output:** `tests/result_tests/20260109_162046_result_hightamine.json` (Failed/Timeout)

## 2. API Result Analysis
The latest API output provided for "Hightamine" is:
```json
    {
      "input_name": "Hightamine",
      "official_name": null,
      "sdk": null,
      "active_ingredient": null,
      "usage": "N/A",
      "contraindications": null,
      "dosage": null,
      "source": "Web",
      "confidence": 0.8,
      "source_urls": [],
      "is_duplicate": false
    }
```
**Observations:**
1.  **Status:** "Found" (Confidence 0.8, Source: Web) - This likely indicates the system *attempted* a web search but reverted to a basic fallback or found a search result listing but failed to parse the detail page.
2.  **Data Missing:** All critical fields (`official_name`, `sdk`, `active_ingredient`) are NULL.
3.  **Source URLs:** Empty. This confirms no detail page was successfully scraped.

## 3. Root Cause Investigation
- **Manual Verification:** The manual playwright test script timed out when attempting to search/extract on `trungtamthuoc.com`.
- **Selector Issue:** The site structure for `input[id='txtKeywords']` or the result container `.cs-item-product` may have changed, or the search response is too slow (>30s).
- **Data Availability:** It is possible "Hightamine" is not indexed correctly on the site's internal search, or requires a specific query variance (e.g. "Hightamine 100mg" vs "Hightamine").

## 4. Conclusion & Recommendations
- **Conclusion:** The current scraper config for `trungtamthuoc.com` is failing to extract "Hightamine". The API correctly flags it as a "Web" result but fails to enrich it.
- **Action Items:**
    1.  **Debug Scraper:** Update `trungtamthuoc` selectors in `app/service/crawler/config.py` (specifically Search Input and Result List).
    2.  **Fallback Strategy:** Ensure Google Search (Advanced) is triggering. The API result shows "Web" not "Web Search (Advanced)", suggesting the Google Fallback might not have fired or found results either.
    3.  **Manual Check:** Verify if "Hightamine" exists on `trungtamthuoc` via a real browser to confirm if it's a data gap or technical gap.
