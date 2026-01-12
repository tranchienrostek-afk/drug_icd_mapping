# AI SCIENTIST LAB NOTES

## 1. Experiment Log (Drug Identification)

### [EXP_04] DataCore Vector Optimization (Smart Search)
- **Date:** 2026-01-09
- **Objective:** Tối ưu hóa Vector Search cho tập dữ liệu lớn (65k records) để tìm kiếm Semantic chính xác hơn.
- **Problem:** Index cũ gộp chung `Tên + Hoạt chất + SDK`. SDK ("VN-...") gây nhiễu Vector Space khi user chỉ search tên thuốc (ngắn).
- **Hypothesis:** Loại bỏ SDK khỏi `search_text` và giãm Threshold sẽ tăng độ chính xác (Recall).
- **Method:**
  1. Re-index 65k thuốc: `search_text = normalize(Ten + HoatChat)`.
  2. Index SDK riêng cho Exact/Regex match.
  3. Tune Threshold: 0.85 -> 0.75.
  4. Add RapidFuzz cho Typo correction ("Paretamol").
- **Result:**
  - ✅ **Exact:** "Paracetamol 500mg" -> 0.06s.
  - ✅ **Vector:** "Tra Hoang Bach Phong" -> Found (Confidence 0.85).
  - ✅ **Fuzzy:** "Paretamol" -> Found (Confidence 94%).
- **Conclusion:** ✅ DEPLOYED in Task 018.

### [EXP_03] Multi-Site Robust Search & Section Extraction
- **Date:** 2026-01-08
- **Objective:** Ensure accurate extraction of detailed fields across multiple sites.
- **Result:** ✅ ACCEPTED. Integrated into `web_crawler.py`.

### [EXP_02] Fuzzy Matching Benchmark
- **Date:** 2026-01-07
- **Result:** Initial benchmark showed need for Semantic Search. (Superseded by EXP_04).

## 2. Current Algorithm Pipeline (Updated v2.0)
```python
def search_drug_smart(query):
    # 1. Exact Match (SQL) - 100% confidence
    if found: return result
    
    # 2. SDK Match (Regex) - 100% confidence
    # (If query looks like SDK)
    
    # 3. Partial Match (SQL LIKE) - 95% confidence
    
    # 4. Fuzzy Match (RapidFuzz) - 85-90% confidence
    # Bắt lỗi chính tả: Paretamol -> Paracetamol
    
    # 5. Vector Search (TF-IDF) - 75-85% confidence
    # Semantic/No-accent: Tra Hoang Bach Phong
    
    # 6. Web Search Fallback (Playwright)
    # Slow (>30s), last resort.
```