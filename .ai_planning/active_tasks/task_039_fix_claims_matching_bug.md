# Task 039: Fix Claims-Medicine Matching Logic (Critical Bug)

**Status**: Planning
**Priority**: 🔴 CRITICAL (Blocker for Demo)
**Related Bug**: `.issues/active/BUG-23-01-2026-01.md`
**Created**: 2026-01-23

---

## 1. Mô tả Vấn đề

### Triệu chứng
API `/api/v1/mapping/match` trả về kết quả **SAI HOÀN TOÀN**:
- **0/6 items matched** (thực tế phải ≥ 4/6)
- **Confidence = 0** cho tất cả items
- **Processing time = 59-65 giây** (quá chậm)
- **Decision = "rejected"** cho tất cả (nguy hiểm pháp lý)

### Log Analysis (Bằng chứng từ Server Logs)

**File log:** `logs/logs_api/23_01_2026_api.log`

```
[2026-01-23 04:08:24] [GET] /api/v1/mapping/health
Duration: 7.230s ← DrugMatcher init cache lần đầu
Status: 200

[2026-01-23 04:08:36] [POST] /api/v1/mapping/test
Duration: 0.208s ← Test single drug OK
Status: 200

[2026-01-23 04:13:28] [POST] /api/v1/mapping/match  ← 🔴 THE FAILED CALL
Duration: 65.130s ← QUÁ CHẬM! (Target: <5s)
Status: 200 ← Không crash, nhưng output SAI
```

**Docker Container Log:**
```
[DrugMatcher] Loaded 83483 drugs into cache ✅
INFO: POST /api/v1/mapping/match HTTP/1.1 200 OK
```

**Kết luận từ Log:**
1. ✅ DrugMatcher cache **loaded thành công** (83k drugs)
2. ✅ API **không crash** (200 OK)
3. ❌ **Matching logic fail** - trả về 0 match dù có data
4. ❌ **Performance bottleneck** - 65s cho 12 items (5.4s/item)

**Root Cause Analysis:**
- Hàm `_enrich_items()` gọi `matcher.match()` cho **TỪNG item** → 12 calls × ~5s = 60s+
- Matching chỉ dựa vào DB lookup, không có **Direct Fuzzy Comparison** giữa Claims & Medicine
- Khi DB không tìm thấy exact match → trả về `NOT_FOUND` thay vì so sánh trực tiếp

### Ví dụ sai nghiêm trọng

| Claim | Medicine | Kết quả hiện tại | Kết quả đúng |
|-------|----------|------------------|--------------|
| Augmentin 875/125 | Amoxicillin + Clavulanic 875/125 | ❌ NO_MATCH | ✅ MATCHED (cùng thuốc) |
| Paracetamol 500 | Para 500mg | ❌ NO_MATCH | ✅ MATCHED (viết tắt) |
| Vitamin B Complex | Vitamin B1 B6 B12 | ❌ NO_MATCH | ⚠️ PARTIAL_MATCH |
| Men tiêu hóa | Probiotic | ❌ NO_MATCH | ⚠️ WEAK_MATCH |
| Thuốc ho thảo dược | Siro ho Prospan | ❌ NO_MATCH | ⚠️ PARTIAL_MATCH |

---

## 2. Phân tích Nguyên nhân Gốc (Root Cause)

### 2.1 Bug trong `service.py` - Matching Logic

**File:** `app/mapping_drugs/service.py`

**Vấn đề 1:** Hàm `_match_claim_to_medicine()` không tìm được match vì:
- Chỉ so sánh `normalized` name → Miss case khác tên nhưng cùng thuốc
- Không sử dụng RapidFuzz để compare trực tiếp Claims vs Medicine
- Chỉ dựa vào DB lookup → Nếu DB không có, fail ngay

**Vấn đề 2:** Hàm `_fuzzy_match_in_list()` có threshold 80 nhưng không được gọi đúng cách

**Vấn đề 3:** `confidence = 0` vì:
- Khi không tìm thấy match, trả về mặc định 0
- Không tính `text_similarity` khi compare Claims vs Medicine trực tiếp

### 2.2 Bug trong `_build_lookup()` - Lookup Dict quá strict

**Vấn đề:** Chỉ lookup bằng exact normalized name, không fuzzy

### 2.3 Thiếu Direct Matching Layer

**Vấn đề:** Hệ thống phụ thuộc 100% vào DB matching.
Nếu thuốc không có trong DB → Fail.

**Giải pháp:** Cần thêm layer **Direct Claims-Medicine Comparison** (không qua DB):
1. Normalize cả 2 danh sách
2. Fuzzy match trực tiếp giữa 2 list
3. DB chỉ là *enrichment*, không phải *requirement*

---

## 3. Kế hoạch Sửa (Implementation Plan)

### Phase 1: Fix Core Matching Logic (High Priority)

#### 1.1 Thêm Direct Fuzzy Comparison
**File:** `app/mapping_drugs/service.py`

```python
def _direct_fuzzy_match(self, claim_service: str, medicine_service: str) -> float:
    """So sánh trực tiếp Claim vs Medicine bằng RapidFuzz."""
    from rapidfuzz import fuzz
    
    claim_norm = normalize_for_matching(claim_service)
    medicine_norm = normalize_for_matching(medicine_service)
    
    # Multiple scores
    ratio = fuzz.ratio(claim_norm, medicine_norm) / 100
    token_sort = fuzz.token_sort_ratio(claim_norm, medicine_norm) / 100
    partial = fuzz.partial_ratio(claim_norm, medicine_norm) / 100
    
    # Best of scores
    return max(ratio, token_sort, partial)
```

#### 1.2 Sửa `_match_claim_to_medicine()` - Thêm Direct Comparison
```python
# BEFORE: Chỉ dựa vào lookup dict
matched_med = lookup.get(claim_normalized)

# AFTER: Thêm direct comparison fallback
if not matched_med:
    # Try direct fuzzy match với tất cả medicine items
    best_score = 0
    best_match = None
    for med in medicines:
        score = self._direct_fuzzy_match(claim['service'], med['service'])
        if score > best_score and score >= 0.6:
            best_score = score
            best_match = med
    if best_match:
        matched_med = best_match
```

### Phase 2: Fix Confidence Calculation

#### 2.1 Confidence không bao giờ = 0 nếu có match attempt
```python
# Minimum confidence khi có fuzzy/ontology enabled
MIN_CONFIDENCE = 0.3

if not matched_med:
    # Vẫn tính text_similarity cao nhất tìm được
    best_similarity = self._find_best_similarity(claim, medicines)
    confidence = max(MIN_CONFIDENCE, best_similarity * 0.5)
```

### Phase 3: Fix Decision Logic (Safety)

#### 3.1 Thay "rejected" bằng "flagged" hoặc "manual_review"
```python
# BEFORE
def _decide(self, confidence: float):
    ...
    else:
        return "no_match", "rejected"  # ❌ DANGEROUS

# AFTER
def _decide(self, confidence: float):
    ...
    else:
        return "no_match", "flagged_for_review"  # ✅ SAFE
```

### Phase 4: Performance Optimization

#### 4.1 Batch DB lookup thay vì 1-by-1
```python
# BEFORE: Loop từng item
for item in items:
    db_result = self.matcher.match(item['service'])

# AFTER: Batch query
services = [item['service'] for item in items]
db_results = self.matcher.match_batch(services)
```

---

## 4. Checklist Thực thi

### Phase 1: Core Fix
- [ ] Thêm hàm `_direct_fuzzy_match()` vào `service.py`
- [ ] Sửa `_match_claim_to_medicine()` để fallback to direct comparison
- [ ] Sửa `_build_lookup()` để support fuzzy lookup

### Phase 2: Confidence Fix
- [ ] Thêm `MIN_CONFIDENCE = 0.3`
- [ ] Sửa logic calculate confidence khi no match

### Phase 3: Safety Fix
- [ ] Thay `"rejected"` → `"flagged_for_review"`
- [ ] Thêm warning log khi risk_level = high

### Phase 4: Performance
- [ ] Implement batch DB lookup
- [ ] Add caching for repeated queries

### Phase 5: Verification
- [ ] Test với sample data từ bug report
- [ ] Verify ≥ 4/6 items matched
- [ ] Verify processing time < 5 seconds
- [ ] Check no "rejected" decisions

---

## 5. Test Data (từ Bug Report)

### Input
```json
{
  "claims": [
    {"claim_id": "clm-001", "service": "Augmentin 875mg + 125mg", "amount": 185000},
    {"claim_id": "clm-002", "service": "Paracetamol 500", "amount": 12000},
    {"claim_id": "clm-003", "service": "Vitamin B Complex", "amount": 45000},
    {"claim_id": "clm-004", "service": "Cefixim 200mg", "amount": 98000},
    {"claim_id": "clm-005", "service": "Men tiêu hóa", "amount": 35000},
    {"claim_id": "clm-006", "service": "Thuốc ho thảo dược", "amount": 68000}
  ],
  "medicine": [
    {"medicine_id": "med-101", "service": "Amoxicillin + Acid Clavulanic 875/125mg", "amount": 180000},
    {"medicine_id": "med-102", "service": "Para 500mg", "amount": 10000},
    {"medicine_id": "med-103", "service": "Vitamin B1 B6 B12", "amount": 47000},
    {"medicine_id": "med-104", "service": "Probiotic", "amount": 36000},
    {"medicine_id": "med-105", "service": "Thuốc bổ gan", "amount": 120000},
    {"medicine_id": "med-106", "service": "Siro ho Prospan", "amount": 72000}
  ]
}
```

### Expected Output (Summary)
```json
{
  "matched_items": 4,
  "need_manual_review": 4,
  "unmatched_claims": 1,
  "risk_level": "medium"
}
```

---

## 6. Definition of Done

- [ ] ≥ 4/6 claims matched với medicine tương ứng
- [ ] Confidence score > 0 cho tất cả items có fuzzy match
- [ ] Processing time < 5 seconds cho 12 items
- [ ] Không có `decision: "rejected"` trong output
- [ ] Bug report `.issues/active/BUG-23-01-2026-01.md` được move sang `resolved/`
