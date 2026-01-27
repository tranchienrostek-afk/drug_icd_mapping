# Implementation Plan: Task 048 - AI Matcher Update for Medical Supplies

## Mục tiêu
Cập nhật logic `AISemanticMatcher` để **MỞ RỘNG phạm vi matching**:
- **Chấp nhận**: Thuốc, Thực phẩm chức năng (TPCN), Vật tư y tế (VTYT), Thiết bị y tế (TBYT).
- **Chỉ loại bỏ**: Dịch vụ kỹ thuật, công khám, xét nghiệm, chẩn đoán hình ảnh, giường bệnh...

## Proposed Changes

### [MODIFY] [app/mapping_drugs/ai_matcher.py](file:///C:/Users/Admin/Desktop/drug_icd_mapping/fastapi-medical-app/app/mapping_drugs/ai_matcher.py)

#### Cập nhật `DRUG_MATCHING_SYSTEM_PROMPT`
Sửa đổi **BƯỚC 1: PHÂN LOẠI CLAIM**:

**Hiện tại:**
> Nếu claim KHÔNG PHẢI là thuốc (dịch vụ kỹ thuật, xét nghiệm, thăm dò chức năng…) → KHÔNG được ghép...

**Mới:**
> **BƯỚC 1: LỌC ĐỐI TƯỢNG (SCOPE FILTERING)**
> - **Chấp nhận so khớp**:
>   1. Thuốc (Drugs)
>   2. Thực phẩm chức năng (Supplements)
>   3. Vật tư y tế (Medical Supplies) - vd: Bơm tiêm, bông băng, que test, dung dịch sát khuẩn, xịt mũi...
>   4. Thiết bị y tế (Medical Equipment)
>
> - **Chỉ loại bỏ (NO MATCH)** nếu là DỊCH VỤ:
>   - Công khám, tư vấn
>   - Xét nghiệm (Lab tests)
>   - Chẩn đoán hình ảnh (X-quang, Siêu âm...)
>   - Thủ thuật, phẫu thuật
>   - Giường bệnh, suất ăn...

### [NEW] [unittest/test_ai_matcher_vtyt.py](file:///C:/Users/Admin/Desktop/drug_icd_mapping/fastapi-medical-app/unittest/test_ai_matcher_vtyt.py)

Tạo file test mới với 10 test cases:

1.  **VTYT Basic**: "Xlear nasal spray" vs "Xlear nasal spray" -> MATCH
2.  **VTYT Generic**: "Bơm tiêm 5ml" vs "Bơm tiêm nhựa 5ml" -> MATCH
3.  **Service Exclusion**: "Công khám bệnh" vs "Panadol" -> NO MATCH
4.  **Lab Exclusion**: "Xét nghiệm máu" vs "Kim lấy máu" -> NO MATCH
5.  **Drug Basic**: "Panadol" vs "Paracetamol" -> MATCH
6.  **Supply vs Drug**: "Bơm tiêm" vs "Thuốc tiêm A" -> NO MATCH
7.  **TPCN**: "Vitamin C" vs "C sủi" -> MATCH
8.  **TBYT**: "Máy đo huyết áp" vs "Máy Omron" -> MATCH
9.  **Ambiguous**: "Dung dịch NaCl 0.9%" (có thể là dịch truyền hoặc rửa) vs "Nước muối sinh lý" -> MATCH
10. **Mixed List**: Batch gồm cả thuốc, VTYT và Dịch vụ -> AI phân loại đúng từng món.

## Verification Plan
1.  Chạy unit test mới:
    ```bash
    pytest unittest/test_ai_matcher_vtyt.py -v
    ```
2.  Verify logs để đảm bảo prompt mới được load.
