# 📋 TÀI LIỆU YÊU CẦU BÀI TOÁN: HỆ THỐNG ĐỐI SOÁT THUỐC YÊU CẦU BỒI THƯỜNG

**Phiên bản:** 1.1.0  
**Ngày:** 2026-01-23  
**Trạng thái:** Draft - Chờ duyệt  

---

## 1. TÓM TẮT BÀI TOÁN (Executive Summary)

### 1.1 Bối cảnh Nghiệp vụ

Trong lĩnh vực **Bảo hiểm Y tế**, một thách thức lớn là đối soát giữa:
- **Danh sách Claims (Yêu cầu bồi thường):** Những loại thuốc mà khách hàng kê khai để yêu cầu công ty bảo hiểm chi trả.
- **Danh sách Medicine (Hóa đơn mua thuốc thực tế):** Những loại thuốc mà khách hàng thực sự đã mua tại nhà thuốc/bệnh viện.

**Vấn đề cốt lõi:** Hai danh sách này thường **không khớp nhau** về mặt tên gọi, mặc dù bản chất có thể là cùng một loại thuốc. Điều này xảy ra vì:
- Cùng một hoạt chất nhưng khác tên thương mại (vd: "Hapacol 500mg" vs "Paracetamol 500mg").
- Khác cách viết tắt (vd: "Para 500" vs "Paracetamol 500mg").
- Sai chính tả hoặc thiếu thông tin (vd: "Vitamin B Cplex" vs "Vitamin B1 B6 B12").
- Gian lận: Khách hàng kê khai thuốc mà họ không mua.

### 1.2 Mục tiêu Hệ thống

Xây dựng một hệ thống tự động có khả năng:

1. ✅ **So khớp thông minh (Intelligent Matching):** Nhận diện cùng bản chất thuốc dù tên khác nhau.
2. ✅ **Phát hiện Gian lận (Fraud Detection):** Cảnh báo các trường hợp Claim mà không có mua thực tế.
3. ✅ **Đưa ra Quyết định (Decision Making):** Tự động phê duyệt (Auto-Approve), yêu cầu xem xét thủ công (Manual Review), hoặc từ chối (Reject).
4. ✅ **Tốc độ cao (High Performance):** Xử lý hàng ngàn cặp thuốc trong vài giây.

---

## 2. PHÂN LOẠI KẾT QUẢ MONG ĐỢI (Expected Outcomes)

| Trạng thái | Mô tả | Hành động |
|---|---|---|
| 🟢 **MATCHED** | Thuốc trong Claim khớp hoàn toàn hoặc tương đương với thuốc trong Medicine. | Auto-Approve |
| 🟡 **PARTIALLY_MATCHED** | Thuốc có độ tương đồng cao (>70%) nhưng không chắc chắn 100%. | Manual Review |
| 🔴 **CLAIM_WITHOUT_PURCHASE** | Thuốc có trong Claim nhưng **KHÔNG CÓ** trong danh sách mua. | **Cảnh báo Gian lận (High Risk)** |
| 🔵 **PURCHASE_WITHOUT_CLAIM** | Thuốc có trong danh sách mua nhưng **KHÔNG CÓ** trong Claim. | Bỏ qua (Khách không yêu cầu bồi thường) |

---

## 3. ĐỊNH DẠNG DỮ LIỆU (Data Formats)

### 3.1 Dữ liệu Đầu vào (Input)

**File:** `input.json`

```json
{
  "request_id": "string",
  "claims": [
    {
      "claim_id": "string (unique)",
      "service": "string (tên thuốc/dịch vụ)",
      "description": "string (mô tả chi tiết)",
      "amount": number (số tiền VND)
    }
  ],
  "medicine": [
    {
      "medicine_id": "string (unique)",
      "service": "string (tên thuốc trên hóa đơn)",
      "description": "string",
      "amount": number
    }
  ]
}
```

### 3.2 Dữ liệu Đầu ra (Output)

**File:** `output.json`

```json
{
  "request_id": "string",
  "status": "processed",
  "summary": {
    "total_claim_items": number,
    "total_medicine_items": number,
    "matched_items": number,
    "unmatched_claims": number,
    "unclaimed_purchases": number,
    "need_manual_review": number,
    "risk_level": "low" | "medium" | "high"
  },
  "results": [
    {
      "claim_id": "string",
      "medicine_id": "string | null",
      "claim_service": "string",
      "medicine_service": "string | null",
      "match_status": "matched" | "partially_matched" | "weak_match" | "no_match",
      "confidence_score": number (0.0 - 1.0),
      "decision": "auto_approved" | "manual_review" | "rejected",
      "evidence": {
        "text_similarity": number,
        "amount_similarity": number,
        "drug_knowledge_match": boolean | "partial",
        "notes": "string (giải thích bằng tiếng Việt)"
      }
    }
  ],
  "anomalies": {
    "claim_without_purchase": [...],
    "purchase_without_claim": [...]
  }
}
```

---

## 4. KIẾN TRÚC GIẢI PHÁP (Solution Architecture)

### 4.1 Luồng Xử lý 3 Bước (3-Step Pipeline)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           INPUT.JSON                                │
│           (Claims List + Medicine List)                             │
└───────────────────────────┬─────────────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│ BƯỚC 1: DATABASE MAPPING (Fast Layer - <200ms)                    │
│ ─────────────────────────────────────────────────────────────────  │
│ • Chuẩn hóa tên thuốc (lowercase, bỏ dấu, bỏ noise words)        │
│ • Tìm kiếm trong Database nội bộ 80k+ thuốc                       │
│ • Output: Bổ sung trường `db_mapping_status` cho mỗi item         │
└───────────────────────────┬─────────────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│ BƯỚC 2: WEB SEARCH (Fallback Layer - <3s, Async)                  │
│ ─────────────────────────────────────────────────────────────────  │
│ • CHỈ CHẠY KHI: Bước 1 trả về NOT_FOUND hoặc confidence < 0.8    │
│ • Nguồn: Google Search API, Bing, Wikipedia, DrugBank             │
│ ⚠️ CẤM: Không dùng thuocbietduoc.com.vn (quá chậm)                │
└───────────────────────────┬─────────────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│ BƯỚC 3: AI MATCHING & SYNTHESIS (Intelligence Layer)             │
│ ─────────────────────────────────────────────────────────────────  │
│ • Tổng hợp dữ liệu từ Bước 1 & 2                                  │
│ • So khớp Claims với Medicine dựa trên hoạt chất, hàm lượng      │
│ • Phát hiện gian lận, tính confidence score                       │
│ • Output: Ghi kết quả vào output.json                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Chiến thuật So khớp (Matching Strategy)

| Tầng | Phương pháp | Confidence |
|---|---|---|
| 1 | **Exact ID Match:** `claim_id == medicine_id` | 100% |
| 2 | **Exact Name Match:** Tên thuốc chuẩn hóa giống nhau hoàn toàn | 95-100% |
| 3 | **Brand vs Generic:** Cùng hoạt chất, khác tên thương mại | 85-95% |
| 4 | **Dosage Normalization:** "500mg" = "0.5g" = "500 mg" | 80-90% |
| 5 | **Fuzzy Text Match:** RapidFuzz token_sort_ratio >= 85 | 70-88% |
| 6 | **TF-IDF Vector Match:** Cosine similarity > 0.75 | 90% |

---

## 5. LOGIC TRIỂN KHAI CHI TIẾT (Implementation Logic)

> ⚠️ **LƯU Ý:** Phần này cung cấp code **độc lập (standalone)**, không phụ thuộc vào API `/drugs/identify` hay `/drugs/agent-search`.

### 5.1 Chuẩn hóa Tên Thuốc (Normalization)

```python
import re
import unicodedata

def normalize_for_matching(text: str) -> str:
    """
    Chuẩn hóa tên thuốc để fuzzy match:
    - Lowercase
    - Bỏ dấu tiếng Việt
    - Giữ lại: a-z, 0-9, space, -, +, %, .
    - Bỏ leading zeros (05ml -> 5ml)
    """
    if not text:
        return ""

    text = text.lower()
    
    # Bỏ dấu tiếng Việt
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = text.replace('đ', 'd')

    # Thay separators
    text = text.replace("/", " ")
    text = re.sub(r'[\(\)\[\]]', ' ', text)

    # Chỉ giữ ký tự hợp lệ
    text = re.sub(r'[^a-z0-9\s\-\+\%\.]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Bỏ leading zeros: 05ml -> 5ml
    def strip_leading_zeros(match):
        num = match.group(1).lstrip('0') or '0'
        suffix = match.group(2) or ''
        return num + suffix
    
    text = re.sub(r'\b0+(\d+)(ml|mg|mcg|g|iu|ui|l|%)?', 
                  strip_leading_zeros, text, flags=re.IGNORECASE)
    
    return text
```

### 5.2 Drug Matcher Class (Multistage Search)

```python
import sqlite3
import numpy as np
from rapidfuzz import process, fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class DrugMatcher:
    """
    Multistage Drug Matcher (Standalone - No API calls)
    
    Flow:
    1. Exact Match (100%)
    2. Partial/LIKE Match (95%)
    3. RapidFuzz (88%)
    4. TF-IDF Vector (90%)
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.vectorizer = None
        self.tfidf_matrix = None
        self.drug_cache = []
        self.fuzzy_names = []
        self._load_cache()
    
    def _load_cache(self):
        """Load drugs vào RAM cho fuzzy/vector search"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, ten_thuoc, so_dang_ky, hoat_chat, search_text 
                FROM drugs 
                WHERE is_verified=1 AND so_dang_ky IS NOT NULL AND so_dang_ky != ''
            """)
            rows = cursor.fetchall()
            self.drug_cache = [dict(row) for row in rows]
            
            if self.drug_cache:
                corpus = [d['search_text'] or d['ten_thuoc'] for d in self.drug_cache]
                self.vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
                self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
                self.fuzzy_names = [d['ten_thuoc'] for d in self.drug_cache]
                print(f"[DrugMatcher] Loaded {len(self.drug_cache)} drugs into cache")
        finally:
            conn.close()
    
    def match(self, drug_name: str) -> dict:
        """
        Tìm thuốc trong DB theo thứ tự ưu tiên.
        
        Returns: {
            "status": "FOUND" | "NOT_FOUND",
            "data": {...} | None,
            "confidence": float,
            "method": str
        }
        """
        raw_query = drug_name.strip()
        normalized = normalize_for_matching(drug_name)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # === LEVEL 1: EXACT MATCH ===
            cursor.execute("""
                SELECT * FROM drugs 
                WHERE ten_thuoc = ? AND is_verified=1 AND so_dang_ky IS NOT NULL
            """, (raw_query,))
            row = cursor.fetchone()
            if row:
                return {
                    "status": "FOUND",
                    "data": dict(row),
                    "confidence": 1.0,
                    "method": "EXACT_MATCH"
                }
            
            # === LEVEL 2: PARTIAL/LIKE MATCH ===
            cursor.execute("""
                SELECT * FROM drugs 
                WHERE ten_thuoc LIKE ? AND is_verified=1 AND so_dang_ky IS NOT NULL
            """, (f"%{normalized}%",))
            row = cursor.fetchone()
            if row:
                return {
                    "status": "FOUND",
                    "data": dict(row),
                    "confidence": 0.95,
                    "method": "PARTIAL_MATCH"
                }
            
            # === LEVEL 3: RAPIDFUZZ ===
            if self.drug_cache:
                fuzzy_res = process.extractOne(
                    raw_query, self.fuzzy_names, scorer=fuzz.token_sort_ratio
                )
                if fuzzy_res:
                    match_name, score, idx = fuzzy_res
                    if score >= 85.0:
                        match_data = self.drug_cache[idx]
                        cursor.execute("SELECT * FROM drugs WHERE id = ?", (match_data['id'],))
                        full_row = cursor.fetchone()
                        if full_row:
                            return {
                                "status": "FOUND",
                                "data": dict(full_row),
                                "confidence": 0.88,
                                "method": f"FUZZY_MATCH (score={score:.1f})"
                            }
            
            # === LEVEL 4: TF-IDF VECTOR ===
            if self.vectorizer and self.tfidf_matrix is not None:
                query_vec = self.vectorizer.transform([normalized])
                cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                
                if cosine_sim.size > 0:
                    best_idx = np.argmax(cosine_sim)
                    best_score = cosine_sim[best_idx]
                    
                    if best_score > 0.75:
                        match_data = self.drug_cache[best_idx]
                        cursor.execute("SELECT * FROM drugs WHERE id = ?", (match_data['id'],))
                        full_row = cursor.fetchone()
                        if full_row:
                            return {
                                "status": "FOUND",
                                "data": dict(full_row),
                                "confidence": 0.90,
                                "method": f"VECTOR_MATCH (cosine={best_score:.2f})"
                            }
            
            # === NOT FOUND ===
            return {
                "status": "NOT_FOUND",
                "data": None,
                "confidence": 0.0,
                "method": "NO_MATCH"
            }
        
        finally:
            conn.close()
```

### 5.3 Web Search Fallback (Optional)

```python
# Chỉ dùng khi DB không tìm thấy và thực sự cần thiết
# ⚠️ CHẬM: 2-5 giây mỗi thuốc

async def search_drug_on_web(drug_name: str) -> dict:
    """
    Fallback: Tìm thuốc trên web nếu DB không có.
    """
    from app.service.crawler import scrape_drug_web_advanced
    
    try:
        result = await scrape_drug_web_advanced(drug_name)
        if result:
            return {
                "status": "FOUND_VIA_WEB",
                "data": {
                    "ten_thuoc": result.get('ten_thuoc'),
                    "hoat_chat": result.get('hoat_chat'),
                    "chi_dinh": result.get('chi_dinh'),
                },
                "source": result.get('source', 'Web'),
                "confidence": 0.8
            }
    except Exception as e:
        print(f"Web search error: {e}")
    
    return {"status": "NOT_FOUND", "data": None}
```

### 5.4 Cách Sử dụng (Usage Example)

```python
# === FULL STANDALONE USAGE ===

DB_PATH = "C:/Users/Admin/Desktop/drug_icd_mapping/fastapi-medical-app/app/database/medical.db"

# Khởi tạo matcher (load cache 1 lần)
matcher = DrugMatcher(DB_PATH)

# Ví dụ: Match các thuốc trong Claims
claims = [
    {"claim_id": "001", "service": "Betadine Súc họng - 125ml"},
    {"claim_id": "002", "service": "Paracetamol 500mg"},
    {"claim_id": "003", "service": "Vitamin B2 2mg"},
]

for claim in claims:
    result = matcher.match(claim["service"])
    print(f"Claim: {claim['service']}")
    print(f"  Status: {result['status']}")
    print(f"  Method: {result['method']}")
    print(f"  Confidence: {result['confidence']}")
    if result['data']:
        print(f"  Matched: {result['data']['ten_thuoc']}")
    print()
```

**Output mẫu:**
```
Claim: Betadine Súc họng - 125ml
  Status: FOUND
  Method: PARTIAL_MATCH
  Confidence: 0.95
  Matched: Betadine Gargle 125ml

Claim: Paracetamol 500mg
  Status: FOUND
  Method: EXACT_MATCH
  Confidence: 1.0
  Matched: Paracetamol 500mg

Claim: Vitamin B2 2mg
  Status: FOUND
  Method: FUZZY_MATCH (score=92.5)
  Confidence: 0.88
  Matched: Vitamin B2 2mg (Riboflavin)
```

---

## 6. CÁC TRƯỜNG HỢP ĐẶC BIỆT (Edge Cases)

### 6.1 Thuốc cùng công dụng nhưng khác nhóm

| Claims | Medicine | Kết luận |
|---|---|---|
| "Men tiêu hóa" | "Probiotic" | **WEAK_MATCH** (gần nghĩa, cần review) |
| "Thuốc ho thảo dược" | "Siro Prospan" | **PARTIALLY_MATCHED** (cùng công dụng) |

### 6.2 Viết tắt phổ biến

- "Para 500" ↔ "Paracetamol 500mg" ✅
- "Vit B Complex" ↔ "Vitamin B1 B6 B12" ⚠️ (cần xem xét)
- "Betadine Súc họng" ↔ "Povidone-Iodine Gargle" ✅

### 6.3 Gian lận (Fraud Indicators)

| Dấu hiệu | Mức độ Rủi ro |
|---|---|
| Claim có, Medicine không có | 🔴 **HIGH** |
| Giá Claim > 30% so với giá mua thực tế | 🟡 **MEDIUM** |
| Cùng thuốc claim nhiều lần (duplicate) | 🟡 **MEDIUM** |

---

## 7. YÊU CẦU PHI CHỨC NĂNG (Non-Functional Requirements)

### 7.1 Hiệu năng (Performance)

| Chỉ số | Mục tiêu | Tối đa |
|---|---|---|
| Response Time (90th percentile) | < 500ms | 1000ms |
| DB Lookup | < 50ms | 100ms |
| Fuzzy Match (batch 100) | < 200ms | 500ms |
| Web Search (per drug) | < 2s | 3s |

### 7.2 Độ chính xác (Accuracy)

| Chỉ số | Mục tiêu |
|---|---|
| Match Accuracy | ≥ 85% |
| False Positive Rate | < 5% |
| False Negative Rate | < 2% |

---

## 8. DEPENDENCIES (Thư viện cần cài)

```bash
pip install rapidfuzz scikit-learn numpy
```

---

## 9. CHECKLIST BÀN GIAO (Definition of Done)

- [ ] Đã load được cache từ Database (80k+ drugs).
- [ ] Fuzzy Match hoạt động với RapidFuzz.
- [ ] TF-IDF Vector Search hoạt động.
- [ ] Output JSON đúng format đã định nghĩa.
- [ ] Edge cases được xử lý (viết tắt, dấu tiếng Việt).
- [ ] Unit Test coverage > 80%.

---

## 10. TÀI LIỆU THAM KHẢO

| File | Mô tả |
|---|---|
| `descriptions.md` | Mô tả nghiệp vụ gốc từ stakeholder |
| `output.json` | Mẫu output kỳ vọng |
| `solutions_03.md` | Technical Specification cho Dev Team |
| `solutions_04.md` | Hướng dẫn phát triển chi tiết |
| `ai-compare.html` | Demo UI hiển thị kết quả so khớp |

---

**Người soạn:** AI Assistant  
**Người duyệt:** [Pending]
