# Phân Tích `app/api/consult.py`

Cũng giống như `drugs.py`, file `consult.py` đang vi phạm nghiêm trọng nguyên tắc phân tách trách nhiệm (Separation of Concerns).

## Vấn Đề Tìm Thấy

1.  **Truy Cập Database Trực Tiếp (Direct DB Access)**:
    - API Handler đang gọi `db.get_connection()` và tự tạo cursor để chạy SQL (dòng 64-90).
    - Câu lệnh SQL phức tạp (`SELECT count(*)... GROUP BY...`) nằm ngay trong code xử lý request.

2.  **Logic Tính Toán (Business Logic)**:
    - Công thức tính độ tin cậy (`conf = math.log10(freq) / 2.0`) nằm hard-code trong API (dòng 99).
    - Logic so khớp (loop lồng nhau giữa thuốc và chẩn đoán) rất phức tạp (dòng 70-111).

3.  **Xử Lý AI & Fallback**:
    - Logic gọi hàm `analyze_treatment_group` và xử lý kết quả trả về, map ngược lại ID thuốc (dòng 126-165) là logic xử lý dữ liệu thuần túy.

## Đề Xuất Refactoring

Cần tạo **`app/service/consultation_service.py`** để chứa toàn bộ logic "Hybrid Consultation" này.

**Cấu trúc Service dự kiến**:
```python
class ConsultationService:
    def check_knowledge_base(self, drug, diagnoses):
        # Chứa SQL query và logic tính confidence
        pass

    async def consult_integrated(self, items, diagnoses):
        # 1. Check KB
        # 2. Collect failed items -> Call AI
        # 3. Merge results
        pass
```

**API Controller** sẽ trở nên rất sạch:
```python
@router.post("/consult_integrated")
async def consult_integrated(payload: ConsultRequest):
    results = await consultation_service.consult_integrated(payload.items, payload.diagnoses)
    return {"results": results}
```
