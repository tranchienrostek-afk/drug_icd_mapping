# 📝 Work Log: AI Enhancements & Robust Mapping Logic

> **Ngày:** 2026-01-27 | **Tác giả:** AI Assistant | **Trạng thái:** Completed

---

## 🎯 Mục tiêu
Nâng cấp khả năng suy luận và xử lý dữ liệu của hệ thống, thay thế các logic regex cứng nhắc bằng AI (Azure OpenAI) và đảm bảo tính nhất quán của dữ liệu thuốc/vật tư y tế.

---

## 🚀 Các thay đổi chính

### 1. AI-Based Role Inference (/api/v1/consult_integrated)
Thay thế logic regex cũ bằng **Azure OpenAI** để phân loại vai trò thuốc từ dữ liệu thô.

- **Vấn đề cũ:** Dữ liệu role trong DB rất hỗn loạn (vd: `["valid", "drug", "main drug"]`, `"{drug"`, `drug, main drug`). Regex không xử lý hết các case.
- **Giải pháp:**
    - Tạo `ai_consult_service.infer_role_from_data(raw_value)`: Gửi raw data cho AI phân tích.
    - **Prompt:** Yêu cầu AI chỉ đích danh Role (main drug, secondary drug...), loại bỏ các từ vô nghĩa (drug, nodrug, valid).
    - **Fallback:** Nếu AI tạch, dùng logic `_fallback_extract_role` đã được cải tiến (fix lỗi artifact `{`).

### 2. Validation & Consistency
Đảm bảo Role và Category luôn logic với nhau (Source of Truth = Role).

- **Logic Mới:** Role quyết định Category & Validity.
- **Rules:**
    - `main drug` / `secondary drug` ➜ **Category: Drug**
    - `supplement` / `medical equipment` ➜ **Category: NoDrug**
- **Safety Net:** Hàm `validate_output()` tự động sửa các case vô lý (vd: `nodrug` + `main drug` ➜ `drug`).

### 3. Hỗ trợ Vật tư & Thiết bị Y tế (/api/v1/mapping/match_v2)
Nâng cấp `AISemanticMatcher` để không bỏ sót VTYT/TBYT.

- **Scope Mới:**
    - ✅ **Chấp nhận Match:** Thuốc, TPCN (Vitamin), Vật tư y tế (Bơm tiêm, bông băng), Thiết bị y tế (Máy đo HA).
    - ❌ **Loại bỏ (No Match):** Dịch vụ kỹ thuật (Khám, Xét nghiệm, X-quang, Giường).
- **Unit Tests:** Đã thêm 10 tests (`test_ai_matcher_vtyt.py`) verify các case này.

### 4. Logic Fallback cho Knowledge Base (Fix KB Empty)
Xử lý lỗi `INTERNAL_KB_EMPTY` khi thuốc có trong DB nhưng chưa map với ICD cụ thể.

- **Vấn đề:** "Ambroxol" điều trị J42 → Nếu trong KB chỉ có "Ambroxol" điều trị J40, hệ thống cũ trả về rỗng (vì sai ICD).
- **Giải pháp:**
    - **Ưu tiên 1:** Tìm chính xác (Drug + ICD).
    - **Fallback:** Nếu không thấy → Tìm theo Drug name (lấy record phổ biến nhất, bỏ qua ICD).
    - **Kết quả:** Luôn trả về thông tin thuốc nếu tên thuốc tồn tại trong hệ thống.

---

## 💻 Chi tiết kỹ thuật

### File Modified
1.  **`app/service/consultation_service.py`**
    - `process_integrated_consultation`: Switch sang dùng AI inference.
    - `_get_valid_role`: Priority logic (TDV > AI > Null).
    - `validate_output`: Logic check chéo role/category.

2.  **`app/service/ai_consult_service.py`**
    - `infer_role_from_data`: Gọi Azure OpenAI.
    - `_fallback_extract_role`: Fix lỗi `{...}` artifact.

3.  **`app/mapping_drugs/ai_matcher.py`**
    - Update `DRUG_MATCHING_SYSTEM_PROMPT` với scope mới.

4.  **`app/service/kb_fuzzy_match_service.py`**
    - `find_best_match_with_icd`: Thêm query fallback (Generic Drug Match).

### Commits
- `b864985`: feat: AI-based role inference
- `6f7f870`: feat: add validate_output()
- `b3f0f4c`: fix: explicit removal of curly braces
- `3331331`: feat: match_v2 support Medical Supplies
- `50dc5ad`: fix: generic drug fallback for KB lookup

---

## 🧪 Kết quả Testing

| Test Suite | Số Test | Trạng thái | Ghi chú |
|------------|---------|------------|---------|
| `test_consult_tdv_fallback.py` | 13 | ✅ PASSED | Cover role inference, TDV feedback priority, validation, artifact cleaning. |
| `test_ai_matcher_vtyt.py` | 10 | ✅ PASSED | Cover VTYT, TBYT, Supplements matching & Service exclusion. |

---

## 🩸 Bài học kinh nghiệm (Lessons Learned)

1.  **Cleaning Artifacts:** Dữ liệu từ Postgres Array (`"{value}"`) rất dễ gây lỗi nếu chỉ parse string đơn giản. Cần xử lý `{}` triệt để.
2.  **Strict vs Relaxed Lookup:** Khớp đúng ICD (Strict) là tốt cho độ chính xác cao, nhưng UX rất tệ nếu thuốc phổ biến mà không hiện ra chỉ vì lệch mã ICD. Fallback ra Generic là bắt buộc.
3.  **Prompt Engineering:** Với AI, việc định nghĩa rõ "Scope" (cái gì nhận, cái gì bỏ) quan trọng hơn là chỉ dẫn cách làm. Prompt mới cho `match_v2` hoạt động tốt nhờ whitelist/blacklist rõ ràng.

---
*Report generated automatically by AI Assistant.*
