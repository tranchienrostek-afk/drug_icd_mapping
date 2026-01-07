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

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "ten_thuoc": "Panadol Extra",
            "so_dang_ky": "VN-12345-67",
            "hoat_chat": "Paracetamol, Caffeine",
            "chi_dinh": "Giảm đau, hạ sốt",
            "cong_ty_san_xuat": "GSK",
            "tu_dong_nghia": "Panadol đỏ, Thuốc giảm đau đầu",
            "modified_by": "admin"
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