# BUG-017: Drug Name Mapping Quality Issues

## 🔴 Vấn Đề
Chất lượng mapping tên thuốc **rất kém**. Chỉ cần thay đổi nhỏ trong input (thêm số 0, thêm khoảng trắng, khác dạng liều...) là không tìm thấy trong KB.

### Ví dụ Minh Họa
| Input | DB Value | Kết Quả | Lý Do |
|-------|----------|---------|-------|
| `proct 03 5ml` | `proct 03 5ml` | ✅ Found | Exact match |
| `proct 03 05ml` | `proct 03 5ml` | ❌ Not Found | `05ml` ≠ `5ml` |
| `proct-03 5ml` | `proct 03 5ml` | ❌ Not Found | Dấu gạch ngang |
| `PROCT 03 5ML` | `proct 03 5ml` | ❓ Depends | Case sensitivity |

---

## 🔍 Root Cause Analysis

### 1. Exact Match Only (Critical)
```python
# consultation_service.py:88
WHERE drug_name_norm = ? AND disease_icd = ?  # <-- EXACT MATCH!
```
- Không có fuzzy matching
- Không có similarity scoring
- Không có fallback nếu exact match fail

### 2. Normalization Gaps
Hàm `normalize_for_matching()` thiếu nhiều case:
- ❌ Leading zeros: `05ml` → `5ml`  
- ❌ Spacing variations: `proct03` vs `proct 03`
- ❌ Unit format: `5 ml` vs `5ml`
- ❌ Separator inconsistency: `-`, `/`, `+`
- ❌ Brand abbreviations: `vit` ↔ `vitamin`

### 3. No Fallback Strategy
- Chỉ query 1 lần với exact match
- Không thử LIKE query
- Không thử FTS search
- Không thử synonym lookup

### 4. No Confidence/Similarity Score
- Không đánh giá mức độ khớp
- Không thể biết match 90% hay 50%
- Không có threshold để quyết định

---

## 📋 Proposed Fix Plan

### Phase 1: Improve Normalization (Quick Wins)
**File:** `app/core/utils.py` → `normalize_for_matching()`

| Rule | Before | After |
|------|--------|-------|
| Leading zeros | `05ml` | `5ml` |
| Spacing | `proct03` | `proct 03` |
| Units | `5 ml` | `5ml` |
| Separators | `drug-name` | `drug name` |
| Decimal dots | `0.5mg` | `0,5mg` or normalize |

### Phase 2: Multi-Level Matching Strategy
**File:** `app/service/consultation_service.py`

```
Level 1: Exact Match (drug_name_norm = ?)
         ↓ (not found)
Level 2: LIKE Match (drug_name_norm LIKE %keyword%)
         ↓ (not found)
Level 3: FTS Search (drugs_fts MATCH ?)
         ↓ (not found)
Level 4: Similarity Match (Levenshtein/Fuzzy)
         ↓ (not found)
Level 5: Return UNKNOWN with suggestions
```

### Phase 3: Fuzzy Matching Algorithm
**New Service:** `app/service/fuzzy_match_service.py`

Options:
1. **Levenshtein Distance** - Simple, built-in possible
2. **RapidFuzz** - Fast, feature-rich library
3. **SQLite FTS5** - Already available, just need proper indexing

**Proposed:** Use combination:
- FTS5 for initial candidates (fast)
- Levenshtein/RapidFuzz for scoring candidates (accurate)

### Phase 4: Synonym & Alias Table
**New Table:** `drug_aliases`

```sql
CREATE TABLE drug_aliases (
    id INTEGER PRIMARY KEY,
    drug_name_norm TEXT,  -- Canonical name in KB
    alias TEXT,           -- Alternative spelling/name
    alias_type TEXT       -- 'abbreviation', 'brand', 'typo', etc.
);
```

---

## ✨ EXISTING SOLUTION FOUND!

**File:** `app/service/drug_search_service.py` → `search_drug_smart_sync()`

Đã có sẵn thuật toán multi-level matching:

```
1. EXACT MATCH       → confidence: 1.0
        ↓
2. PARTIAL LIKE      → confidence: 0.95
        ↓
3. RAPIDFUZZ         → confidence: 0.88 (if score ≥ 85)
        ↓
4. TF-IDF VECTOR     → confidence: 0.90 (if cosine > 0.75)
```

**Tech Stack:**
- `sklearn.TfidfVectorizer` + `cosine_similarity`
- `rapidfuzz.process.extractOne` + `fuzz.token_sort_ratio`
- SQLite FTS5 fallback

---

## 🔧 Implementation Plan (Revised)

### Option A: Reuse DrugSearchService (Recommended ⭐)

**Thay đổi:** `app/service/consultation_service.py`

Thay vì query trực tiếp `knowledge_base` với exact match, ta:
1. Dùng `DrugSearchService.search_drug_smart()` để tìm drug match
2. Sau khi có `drug_name_norm` chuẩn từ DB, query KB với nó

**Pseudocode:**
```python
# consultation_service.py
from app.service.drug_search_service import DrugSearchService

class ConsultationService:
    def __init__(self):
        ...
        self.drug_search = DrugSearchService(self.db_core)
    
    async def process_integrated_consultation(self, request):
        for item in request.items:
            # Step 1: Fuzzy match drug name to get canonical name
            match = await self.drug_search.search_drug_smart(item.name)
            
            if match:
                canonical_name = match['data'].get('ten_thuoc')
                # Step 2: Use canonical name to query KB
                kb_result = self.check_knowledge_base(canonical_name, icds)
            ...
```

### Option B: Build KB-Specific Fuzzy Service

Nếu KB có data khác với `drugs` table → cần service riêng.

Tạo `KnowledgeBaseFuzzyService`:
- Load tất cả `drug_name_norm` từ `knowledge_base`
- Build TF-IDF matrix
- Expose `find_best_match(input_name, disease_icd) -> (canonical_name, score)`

---

## 📋 Action Items

| # | Task | File | Priority |
|---|------|------|----------|
| 1 | Inject `DrugSearchService` vào `ConsultationService` | `consultation_service.py` | P1 |
| 2 | Thay `check_knowledge_base_strict()` bằng 2-step: fuzzy drug → KB query | `consultation_service.py` | P1 |
| 3 | Add logging để debug matching quality | `consultation_service.py` | P2 |
| 4 | Test với các case trong bug report | unittest | P2 |

---

## 📝 Notes

- **Status:** Ready for Implementation
- **Created:** 2026-01-21
- **Key Insight:** Không cần build mới, reuse `DrugSearchService`!
