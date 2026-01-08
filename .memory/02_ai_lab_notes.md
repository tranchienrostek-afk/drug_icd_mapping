# AI SCIENTIST LAB NOTES

## 1. Experiment Log (Drug Identification)

### [EXP_01] Hybrid Search Strategy
- **Date:** 2026-01-08
- **Objective:** Improve drug identification speed and accuracy.
- **Hypothesis:** Combining Google Search (for URL discovery) + Playwright (for scraping) is faster than internal site search.
- **Method:**
  1. Input: "Symbicort"
  2. Google Search: `site:thuocbietduoc.com.vn Symbicort` -> Get URL
  3. Direct Navigate -> Extract SDK
- **Result:**
  - Google Search API (googlesearch-python) hit rate limits.
  - Accuracy: High (when it works).
  - Speed: Failed due to detailed timeout/blocking.
- **Conclusion:** ❌ REJECTED as primary method due to reliability issues. Need fallback or paid API.

### [EXP_03] Multi-Site Robust Search & Section Extraction
- **Date:** 2026-01-08
- **Objective:** Ensure accurate extraction of detailed fields (indications, dosage, SDK) across multiple pharmaceutical websites despite layout changes and popups.
- **Method:**
  1. Standardize `config.py` with text-based relative selectors.
  2. Implement `handle_popups` in `core_drug.py`.
  3. Generalize `extract_section_range` (H2/H3 block parsing) in `extractors.py`.
- **Result:**
  - ✅ **Accuracy:** Extracted "Augmentin" SDK (VN-20517-17) and Indications successfully.
  - ✅ **Stability:** Closed popups on LongChau and TrungTamThuoc automatically.
  - ✅ **Multi-site:** Merged results from ThuocBietDuoc and TrungTamThuoc correctly.
- **Conclusion:** ✅ ACCEPTED. This architecture provides the necessary robust fallback when Google Search is rate-limited.

### [EXP_02] Fuzzy Matching Benchmark
- **Date:** 2026-01-07
- **Method:** RapidFuzz `token_sort_ratio` on 100 common drugs.
- **Result:** F1-Score: 0.88.
- **Observation:** Good for typo fixing ("Panadol" vs "Paradol"), bad for semantic ("Thuốc hạ sốt" vs "Paracetamol").
- **Next Step:** Implement Semantic Search (Sentence-BERT).

## 2. Current Algorithm Pipeline
```python
def identify_drug(input_text):
    # 1. Normalize
    clean_text = normalize(input_text)
    
    # 2. Database Lookup (Exact + Fuzzy)
    db_result = search_db(clean_text)
    if db_result.confidence > 0.95: return db_result
    
    # 3. Web Scraping (Fallback)
    # Strategy: Google First -> Internal Search Fallback
    web_result = crawler.search(clean_text)
    
    return web_result
```