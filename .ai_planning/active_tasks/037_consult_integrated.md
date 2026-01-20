# Task 037: Implement Consultation API (Integrated KB + AI)

## 1. Overview
Implement `/api/v1/consult_integrated` to validate drug-disease pairs by checking the Internal Knowledge Base. This API serves as a "Check Drug Interaction" feature, prioritizing manual expert feedback (TDV) over ingested AI data.

**Constraint**: **NO External AI Fallback**. If data is not found in the Internal DB, return empty/not found results.

## 2. Input/Output Specification
Strictly follows format defined in `knowledge for agent/to_database/api_consult_integrated.md`.

### Input JSON
```json
{
  "diagnoses": [
    { "code": "R51", "name": "Đau đầu", "type": "MAIN" },
    { "code": "J06.9", "name": "Nhiễm trùng đường hô hấp", "type": "SECONDARY" }
  ],
  "items": [
    { "id": "d1", "name": "Paracetamol 500mg" },
    { "id": "d2", "name": "Amoxicillin 250mg" }
  ],
  "request_id": "REQ-001",
  "symptom": "Đau đầu kèm sốt nhẹ"
}
```

### Output JSON
```json
{
  "results": [
    {
      "category": "drug",
      "explanation": "Expert Verified: Classified as 'Thuốc điều trị chính'...",
      "id": "d1",
      "name": "Paracetamol 500mg",
      "role": "Thuốc điều trị chính",
      "source": "INTERNAL_KB_TDV",
      "validity": "valid"
    }
  ]
}
```

## 3. Implementation Logic

### Component: `ConsultationService`
File: `app/service/consultation_service.py`

#### method: `process_integrated_consultation(request)`

1.  **Normalization**:
    *   Use `app.core.utils.normalize_text` (same as ETL) for `drug_name`.
    *   Use `disease_icd` (uppercase, stripped) for diseases.

2.  **Iterate & Query**:
    *   Loop through each `item` (Drug) vs `diagnosis` (Disease).
    *   Query `knowledge_base` table:
        ```sql
        SELECT * FROM knowledge_base 
        WHERE drug_name_norm = ? AND disease_icd = ?
        ```

3.  **Priority Decision**:
    *   **Priority 1: Expert Feedback (`tdv_feedback`)**
        *   If column `tdv_feedback` is NOT NULL/Empty.
        *   Parse `tdv_feedback` (JSON or String) to extract "validity", "role".
        *   Return `source: INTERNAL_KB_TDV`.
    *   **Priority 2: AI Ingested (`treatment_type`)**
        *   If `tdv_feedback` is missing but `treatment_type` exists.
        *   Return `source: INTERNAL_KB_AI`.

4.  **No Fallback**:
    *   If no record found in DB -> Skip (Do NOT call Azure/OpenAI).

## 4. Work Items

- [x] **Define Models**: `ConsultRequest`, `ConsultResponse` in `app/models.py`.
- [x] **Service Logic**: Implement `process_integrated_consultation` in `ConsultationService` reusing `search_normalizer` logic if applicable.
- [x] **API Endpoint**: Add `POST /integrated` to `app/api/consultation.py`.
- [x] **Unit Tests**: Coverage for exact match (TDV), fallback match (AI), and no match.

## 5. Notes
- Re-use `app.core.utils` for text normalization to ensure mapping consistency with ETL.
- `rowid` issues from ETL debugging must be avoided (use `id` where possible, though `knowledge_base` has its own `id`).
