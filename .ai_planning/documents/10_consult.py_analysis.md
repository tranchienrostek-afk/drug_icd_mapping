# Phân Tích `app/api/consult.py`

> **Trạng thái**: ✅ **ĐÃ REFACTORED** (2026-01-16)

## Tóm Tắt

File `consult.py` đã được refactor thành công. API Controller giờ chỉ đóng vai trò điều phối (thin controller), toàn bộ business logic đã được chuyển sang `ConsultationService`.

---

## Kiến Trúc Hiện Tại

### API Controller (`app/api/consult.py`)
```python
from app.service.consultation_service import ConsultationService

router = APIRouter()
consultation_service = ConsultationService(db_core=db.db_core)

@router.post("/consult_integrated", response_model=ConsultResponse)
async def consult_integrated(payload: ConsultRequest):
    results_data = await consultation_service.consult_integrated(payload.items, payload.diagnoses)
    results = [ConsultResult(**item) for item in results_data]
    return ConsultResponse(results=results)
```

### Service Layer (`app/service/consultation_service.py`)
```python
class ConsultationService:
    def __init__(self, db_core: DatabaseCore = None):
        self.db_core = db_core or DatabaseCore()

    def check_knowledge_base(self, drug_name: str, disease_name: str, disease_type: str) -> Optional[Dict]:
        """Check Internal Knowledge Base (Rule-based) with TDV Priority."""
        # Query both treatment_type (AI) and tdv_feedback (Human)
        # 1. Check for 'tdv_feedback' -> Return immediately (Source: INTERNAL_KB_TDV)
        # 2. Fallback to 'treatment_type' (Source: INTERNAL_KB_AI) if confidence >= 0.8
        pass

    async def consult_integrated(self, items: List, diagnoses: List) -> List:
        """Hybrid Consultation: KB Check → AI Fallback."""
        # 1. Check KB cho từng drug-diagnosis pair
        # 2. Collect unresolved items → Call AI
        # 3. Merge results
        pass

    async def _call_ai_fallback(self, drugs: List, diagnoses: List) -> List:
        """Internal: Call AI service cho các items không tìm thấy trong KB."""
        pass
```

---

## Các Vấn Đề Đã Fix

| # | Vấn đề cũ | Giải pháp |
|---|-----------|-----------|
| 1 | API truy cập DB trực tiếp | ✅ Delegate sang `ConsultationService` |
| 2 | SQL hard-coded trong controller | ✅ Di chuyển vào `check_knowledge_base()` |
| 3 | Logic confidence trong API | ✅ Nằm trong service method |
| 4 | Nested loops phức tạp | ✅ Tách thành methods riêng |
| 5 | AI fallback logic | ✅ Tách thành `_call_ai_fallback()` |

---

## Flow Hiện Tại

```
POST /consult_integrated
        │
        ▼
┌──────────────────┐
│  API Controller  │  (Thin - chỉ parse request/response)
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  ConsultationService     │
│  .consult_integrated()   │
└────────┬─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌────────────┐
│ Check   │ │ AI Fallback│
│ KB      │ │ Service    │
│(Priority│ └────────────┘
│ Logic)  │
└─────────┘
    │
    ├─ 1. Check TDV Feedback (Expert) ✅
    └─ 2. Check AI Classification (Frequency) ⚠️
```

---

## Files Liên Quan

| File | Mô tả |
|------|-------|
| `app/api/consult.py` | API endpoint (thin controller) |
| `app/service/consultation_service.py` | Business logic chính |
| `app/service/ai_consult_service.py` | AI/LLM integration |
| `app/database/core.py` | Database access layer |

---

## Test Coverage

```bash
pytest test_comprehensive_api.py::TestConsultAPI -v
```

- `test_consult_integrated` - Test hybrid consultation
- `test_consult_empty_items` - Test edge case

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | ✅ Refactoring hoàn tất. Service layer đã được tạo. |
| 2026-01-15 | 📝 Phân tích ban đầu, đề xuất refactoring |
