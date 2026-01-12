# DEVELOPER IMPLEMENTATION LOG

## 1. Function Map
- **Search Engine (Backend):** `app/services.py` -> `DrugDbEngine`
  - `search_drug_smart(query)`: Logic lõi, kết hợp Exact -> Fuzzy -> Vector -> Web.
  - `_load_vector_cache()`: Quản lý RAM cache (Name List & TF-IDF Matrix).
  - `DrugDbEngine` class also handles Staging & Verification flow.

- **Scraping Core:** `app/service/crawler/core_drug.py`
  - `scrape_single_site_drug(browser, config, keyword, direct_url)`: Logic cào đơn lẻ.
- **Crawler Main:** `app/service/crawler/main.py`
  - `scrape_drug_web_advanced(keyword, **kwargs)`: Entry point, handles parallel tasks.
- **Google Search:** `app/service/crawler/google_search.py`
  - `GoogleSearchService.find_drug_url(drug_name)`: Trả về URL chi tiết từ Google.

## 2. Implementation Notes
- **Search Optimization (Task 018):**
  - Integrated `rapidfuzz` (Process.extractOne) for typo tolerance.
  - Optimized TF-IDF Vectorizer by removing SDK from search text (reducing noise).
  - Reduced Vector Search threshold to 0.75.
- **Data Import (Task 022):**
  - Script `scripts/run_import_datacore.py` handles 65k records via `DataRefinery`.

- **Headless Bypass:** Đã add args `--disable-blink-features=AutomationControlled` vào `main.py` để qua mặt anti-bot của ThuocBietDuoc.
- **Direct URL Logic:** Trong `core_drug.py`, nếu có `direct_url`, quy trình sẽ nhảy qua bước Search internal, đi thẳng vào `extract_drug_details`.

## 3. Active Challenges
- **RAM Usage:** 65k drugs in-memory vector cache takes ~100MB RAM. Need monitoring as data grows.
- **Selector Fragility:** Layout của ThuocBietDuoc thỉnh thoảng thay đổi class name. Cần monitor.