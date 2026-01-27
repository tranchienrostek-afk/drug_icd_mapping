"""
Pydantic Models cho Claims vs Medicine Matching API
====================================================
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime


# =============================================================================
# INPUT MODELS
# =============================================================================

class ClaimItem(BaseModel):
    """Một dòng trong danh sách Claims (yêu cầu bồi thường)."""
    claim_id: str = Field(..., description="ID duy nhất của claim", alias="id")
    service: str = Field(..., description="Tên thuốc/dịch vụ", alias="service_name")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")
    amount: Optional[float] = Field(None, description="Số tiền (VND)")
    
    model_config = ConfigDict(populate_by_name=True)


class MedicineItem(BaseModel):
    """Một dòng trong danh sách Medicine (hóa đơn mua thuốc)."""
    medicine_id: str = Field(..., description="ID duy nhất của medicine", alias="id")
    service: str = Field(..., description="Tên thuốc trên hóa đơn", alias="service_name")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")
    amount: Optional[float] = Field(None, description="Số tiền (VND)")

    model_config = ConfigDict(populate_by_name=True)


class MatchingRequest(BaseModel):
    """Request body cho API matching."""
    request_id: Optional[str] = Field(None, description="ID của request (để tracking)")
    claims: List[ClaimItem] = Field(..., description="Danh sách Claims")
    medicine: List[MedicineItem] = Field(..., description="Danh sách Medicine", alias="medicines")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


# =============================================================================
# OUTPUT MODELS
# =============================================================================

class MatchEvidence(BaseModel):
    """Bằng chứng cho việc match."""
    text_similarity: Optional[float] = Field(None, description="Độ tương đồng text (0-1)")
    amount_similarity: Optional[float] = Field(None, description="Độ tương đồng giá (0-1)")
    drug_knowledge_match: Optional[bool] = Field(None, description="Match qua DB thuốc")
    method: str = Field(..., description="Phương pháp match đã dùng")
    notes: Optional[str] = Field(None, description="Ghi chú giải thích")


class MatchedPair(BaseModel):
    """Một cặp Claim-Medicine đã match."""
    claim_id: str
    medicine_id: Optional[str] = None
    claim_service: str
    medicine_service: Optional[str] = None
    match_status: Literal["matched", "partially_matched", "weak_match", "no_match"]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    decision: Literal["auto_approved", "manual_review", "rejected"]
    evidence: MatchEvidence


class Anomaly(BaseModel):
    """Bất thường phát hiện được."""
    id: str
    service: str
    amount: Optional[float] = None
    risk_flag: Literal["low", "medium", "high"]
    reason: str


class AnomaliesReport(BaseModel):
    """Báo cáo các bất thường."""
    claim_without_purchase: List[Anomaly] = Field(default_factory=list)
    purchase_without_claim: List[Anomaly] = Field(default_factory=list)


class MatchingSummary(BaseModel):
    """Tóm tắt kết quả matching."""
    total_claim_items: int
    total_medicine_items: int
    matched_items: int
    unmatched_claims: int
    unclaimed_purchases: int
    need_manual_review: int
    risk_level: Literal["low", "medium", "high"]


class AuditTrail(BaseModel):
    """Log các bước xử lý."""
    normalization_applied: bool = True
    fuzzy_matching: bool = True
    drug_ontology_used: bool = True
    amount_used_as_supporting_signal: bool = True
    processing_time_ms: Optional[float] = None


class MatchingResponse(BaseModel):
    """Response body cho API matching."""
    request_id: Optional[str] = None
    status: Literal["processed", "error"] = "processed"
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    summary: MatchingSummary
    results: List[MatchedPair]
    anomalies: AnomaliesReport
    audit_trail: AuditTrail


# =============================================================================
# SIMPLE MODELS (for testing)
# =============================================================================

class DrugMatchRequest(BaseModel):
    """Request đơn giản để test match 1 thuốc."""
    drug_name: str


class DrugMatchResponse(BaseModel):
    """Response cho match 1 thuốc."""
    input_name: str
    status: Literal["FOUND", "NOT_FOUND"]
    official_name: Optional[str] = None
    sdk: Optional[str] = None
    active_ingredient: Optional[str] = None
    confidence: float
    method: str
