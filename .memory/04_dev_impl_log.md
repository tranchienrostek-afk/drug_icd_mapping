# DEVELOPER IMPLEMENTATION LOG

## 1. Function Map
- **Scraping Core:** `app/service/crawler/core_drug.py`
  - `scrape_single_site_drug(browser, config, keyword, direct_url)`: Logic cào đơn lẻ.
- **Crawler Main:** `app/service/crawler/main.py`
  - `scrape_drug_web_advanced(keyword, **kwargs)`: Entry point, handles parallel tasks.
- **Google Search:** `app/service/crawler/google_search.py`
  - `GoogleSearchService.find_drug_url(drug_name)`: Trả về URL chi tiết từ Google.

## 2. Implementation Notes
- **Headless Bypass:** Đã add args `--disable-blink-features=AutomationControlled` vào `main.py` để qua mặt anti-bot của ThuocBietDuoc.
- **Direct URL Logic:** Trong `core_drug.py`, nếu có `direct_url`, quy trình sẽ nhảy qua bước Search internal, đi thẳng vào `extract_drug_details`.
- **Dependencies:**
  - `googlesearch-python`: Dùng cho search. Lưu ý: Library này scrape HTML của Google Search result, dễ bị block IP.

## 3. Active Challenges
- **Rate Limit:** Google chặn request nếu gọi quá nhanh. Cần implement delay hoặc rotation (hoặc chuyển sang SerpAPI).
- **Selector Fragility:** Layout của ThuocBietDuoc thỉnh thoảng thay đổi class name. Cần monitor.