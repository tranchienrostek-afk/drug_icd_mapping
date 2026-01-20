from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class DrugInput(BaseModel):
    name: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Paracetamol"
        }
    })

class DiagnosisInput(BaseModel):
    name: str
    icd10: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Acute pharyngitis",
            "icd10": "J02.9"
        }
    })

class DiseaseRequest(BaseModel):
    diagnosis: List[DiagnosisInput]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "diagnosis": [
                {
                    "name": "Acute pharyngitis",
                    "icd10": "J02.9"
                }
            ]
        }
    })

class DrugRequest(BaseModel):
    drugs: List[str]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "drugs": [
    "Ludox - 200mg",
    "Berodual 200 liều (xịt) - 10ml",
    "Symbicort 120 liều",
    "Althax - 120mg",
    "Hightamine"
  ]
        }
    })

class AnalysisRequest(BaseModel):
    drugs: List[str]
    diagnosis: List[DiagnosisInput]

    model_config = ConfigDict(json_schema_extra={
        "example": {
  "diagnosis": [
    {
      "icd10": "E11",
      "name": "Bệnh đái tháo đường không phụ thuộc insuline"
    },
    {
      "icd10": "I10",
      "name": "Bệnh Tăng huyết áp vô căn (nguyên phát)"
    },
    {
      "icd10": "R51",
      "name": "Đau đầu"
    },
    {
      "icd10": "G47",
      "name": "Rối loạn giấc ngủ"
    },
    {
      "icd10": "L20",
      "name": "Viêm da cơ địa"
    }
  ],
  "drugs": [
    "Candesartan + hydrochlorothiazid 16mg + 12.5mg",
    "Cetirizin 10mg",
    "Rotundin 60mg",
    "Paracetamol (acetaminophen) 500mg"
  ]
}
    })

class DrugConfirmRequest(BaseModel):
    ten_thuoc: str
    so_dang_ky: str
    hoat_chat: str
    chi_dinh: str
    cong_ty_san_xuat: str
    tu_dong_nghia: Optional[str] = None
    modified_by: Optional[str] = "system"

# --- Consult Models ---
class DrugItem(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "d1",
            "name": "Paracetamol 500mg"
        }
    })

class DiagnosisItem(BaseModel):
    code: str
    name: str
    type: str  # MAIN / SECONDARY

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": "R51",
            "name": "Đau đầu",
            "type": "MAIN"
        }
    })

class ConsultRequest(BaseModel):
    request_id: str
    items: List[DrugItem]
    diagnoses: List[DiagnosisItem]
    symptom: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "request_id": "REQ-001",
            "items": [
                {"id": "d1", "name": "Paracetamol 500mg"},
                {"id": "d2", "name": "Amoxicillin 250mg"}
            ],
            "diagnoses": [
                {"code": "R51", "name": "Đau đầu", "type": "MAIN"},
                {"code": "J06.9", "name": "Nhiễm trùng đường hô hấp", "type": "SECONDARY"}
            ],
            "symptom": "Đau đầu kèm sốt nhẹ"
        }
    })

class ConsultResult(BaseModel):
    id: str
    name: str
    category: str = "drug"
    validity: str
    role: str
    explanation: str
    source: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "d1",
            "name": "Paracetamol 500mg",
            "category": "drug",
            "validity": "valid",
            "role": "Thuốc điều trị chính",
            "explanation": "Internal KB (AI): Found 150 records. Confidence: 95%",
            "source": "INTERNAL_KB_AI"
        }
    })

class ConsultResponse(BaseModel):
    results: List[ConsultResult]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "results": [
                {
                    "id": "d1",
                    "name": "Paracetamol 500mg",
                    "category": "drug",
                    "validity": "valid",
                    "role": "Thuốc điều trị chính",
                    "explanation": "Expert Verified: Classified as 'Thuốc điều trị chính' by Medical Reviewer.",
                    "source": "INTERNAL_KB_TDV"
                },
                {
                    "id": "d2",
                    "name": "Amoxicillin 250mg",
                    "category": "drug",
                    "validity": "valid",
                    "role": "Thuốc hỗ trợ",
                    "explanation": "AI Suggestion: Phù hợp với nhiễm trùng đường hô hấp",
                    "source": "EXTERNAL_AI"
                }
            ]
        }
    })

class DrugStagingUpdateRequest(BaseModel):
    ten_thuoc: Optional[str] = None
    so_dang_ky: Optional[str] = None
    hoat_chat: Optional[str] = None
    cong_ty_san_xuat: Optional[str] = None
    chi_dinh: Optional[str] = None
    tu_dong_nghia: Optional[str] = None
    classification: Optional[str] = None
    note: Optional[str] = None
    modified_by: str = "admin"

class DrugStagingResponse(BaseModel):
    id: int
    ten_thuoc: str
    so_dang_ky: str
    hoat_chat: str
    status: str
    created_at: str
    created_by: str
    conflict_type: str # 'sdk' or 'name'
    conflict_id: Optional[int] = None
    conflict_info: Optional[dict] = None # Nested info about the conflicting drug

class DrugHistoryResponse(BaseModel):
    id: int
    original_drug_id: int
    ten_thuoc: str
    so_dang_ky: str
    archived_at: str
    archived_by: str

class DrugDiseaseLinkRequest(BaseModel):
    drug_name: str
    sdk: Optional[str] = None
    original_drug_id: Optional[int] = None # Nếu đã có ID
    disease_name: str
    icd_code: Optional[str] = None
    treatment_note: Optional[str] = None
    is_verified: Optional[int] = 0
    coverage_type: Optional[str] = None # "Thuốc điều trị", "Thuốc hỗ trợ", etc.
    created_by: Optional[str] = "system"
    status: Optional[str] = "active" # 'active' or 'pending'

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sdk": "VN-12345-67",
            "drug_name": "Panadol Extra",
            "icd_code": "R51",
            "disease_name": "Đau đầu",
            "treatment_note": "Paracetamol là lựa chọn đầu tay giảm đau đầu nhẹ đến vừa.",
            "is_verified": 1
        }
    })

class DiseaseConfirmRequest(BaseModel):
    icd_code: str
    disease_name: str
    chapter_name: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "icd_code": "R51",
            "disease_name": "Đau đầu",
            "chapter_name": "Triệu chứng tổng quát"
        }
    })