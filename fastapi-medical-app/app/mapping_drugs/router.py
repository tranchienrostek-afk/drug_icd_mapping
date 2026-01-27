"""
FastAPI Router cho Claims vs Medicine Matching API
===================================================
Endpoints:
- POST /api/v1/mapping/match - Match Claims với Medicine
- POST /api/v1/mapping/test - Test match 1 thuốc
"""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from .service import ClaimsMedicineMatchingService
from .matcher import DrugMatcher
from .models import (
    MatchingRequest, MatchingResponse,
    DrugMatchRequest, DrugMatchResponse
)

router = APIRouter()

# Khởi tạo services (singleton)
_matching_service = None
_drug_matcher = None


def get_matching_service() -> ClaimsMedicineMatchingService:
    """Lazy init matching service."""
    global _matching_service
    if _matching_service is None:
        _matching_service = ClaimsMedicineMatchingService()
    return _matching_service


def get_drug_matcher() -> DrugMatcher:
    """Lazy init drug matcher."""
    global _drug_matcher
    if _drug_matcher is None:
        _drug_matcher = DrugMatcher()
    return _drug_matcher


@router.post("/match", response_model=MatchingResponse)
async def match_claims_medicine(request: MatchingRequest):
    """
    So khớp danh sách Claims với danh sách Medicine.
    
    **Input:**
    - `claims`: Danh sách thuốc yêu cầu bồi thường
    - `medicine`: Danh sách thuốc đã mua thực tế
    
    **Output:**
    - `results`: Danh sách các cặp đã match với confidence score
    - `anomalies`: Các bất thường phát hiện được (gian lận tiềm ẩn)
    - `summary`: Tóm tắt kết quả
    
    **Logic:**
    1. Chuẩn hóa tên thuốc (bỏ dấu, lowercase, bỏ leading zeros)
    2. Map với Database 80k+ thuốc (Exact → Partial → Fuzzy → Vector)
    3. So khớp Claims với Medicine dựa trên tên chuẩn, hoạt chất, giá
    4. Phát hiện Claims không có mua (fraud) và mua không claim (skip)
    """
    if not request.claims:
        raise HTTPException(status_code=400, detail="Claims list cannot be empty")
    
    if not request.medicine:
        raise HTTPException(status_code=400, detail="Medicine list cannot be empty")
    
    try:
        service = get_matching_service()
        result = await service.process(request)
        
        # Manual validation to catch Pydantic errors HERE
        validated_result = MatchingResponse.model_validate(result)
        return validated_result
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        with open("c:\\app\\logs\\mapping\\router_errors.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}] [ROUTER ERROR] /match failed: {e}\n{error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Matching error: {str(e)}")


@router.post("/match_v2", response_model=MatchingResponse)
async def match_claims_medicine_v2(request: MatchingRequest):
    """
    So khớp danh sách Claims với danh sách Medicine - VERSION 2 (DIRECT AI).
    
    **Đặc điểm:**
    - Gửi trực tiếp dữ liệu thô vào AI.
    - Không qua chuẩn hóa, không qua database lookup.
    - AI tự phân tích ngữ nghĩa, hoạt chất và ghép nhóm.
    
    **Input:**
    - `claims`: Danh sách thuốc yêu cầu bồi thường (thô)
    - `medicine`: Danh sách thuốc đã mua thực tế (thô)
    """
    if not request.claims:
        raise HTTPException(status_code=400, detail="Claims list cannot be empty")
    
    if not request.medicine:
        raise HTTPException(status_code=400, detail="Medicine list cannot be empty")
    
    try:
        service = get_matching_service()
        result = await service.process_v2(request)
        
        # Manual validation to catch Pydantic errors HERE
        validated_result = MatchingResponse.model_validate(result)
        return validated_result
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        with open("c:\\app\\logs\\mapping\\router_errors.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}] [ROUTER ERROR] /match_v2 failed: {e}\n{error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Matching V2 error: {str(e)}")


@router.post("/test", response_model=DrugMatchResponse)
async def test_drug_match(request: DrugMatchRequest):
    """
    Test match 1 thuốc với Database.
    
    Dùng để debug và kiểm tra logic matching trước khi chạy batch.
    
    **Input:**
    - `drug_name`: Tên thuốc cần tìm
    
    **Output:**
    - `status`: FOUND hoặc NOT_FOUND
    - `official_name`: Tên chuẩn trong DB (nếu tìm thấy)
    - `confidence`: Độ tin cậy (0-1)
    - `method`: Phương pháp đã dùng để match
    """
    if not request.drug_name or not request.drug_name.strip():
        raise HTTPException(status_code=400, detail="Drug name cannot be empty")
    
    try:
        matcher = get_drug_matcher()
        result = matcher.match(request.drug_name)
        
        data = result.get('data', {}) or {}
        
        return DrugMatchResponse(
            input_name=request.drug_name,
            status=result['status'],
            official_name=data.get('ten_thuoc'),
            sdk=data.get('so_dang_ky'),
            active_ingredient=data.get('hoat_chat'),
            confidence=result['confidence'],
            method=result['method']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Match error: {str(e)}")


@router.post("/batch-test", response_model=List[DrugMatchResponse])
async def test_drug_match_batch(drug_names: List[str]):
    """
    Test match nhiều thuốc cùng lúc.
    
    **Input:**
    - List tên thuốc (strings)
    
    **Output:**
    - List kết quả match
    """
    if not drug_names:
        raise HTTPException(status_code=400, detail="Drug names list cannot be empty")
    
    try:
        matcher = get_drug_matcher()
        results = []
        
        for name in drug_names:
            result = matcher.match(name)
            data = result.get('data', {}) or {}
            
            results.append(DrugMatchResponse(
                input_name=name,
                status=result['status'],
                official_name=data.get('ten_thuoc'),
                sdk=data.get('so_dang_ky'),
                active_ingredient=data.get('hoat_chat'),
                confidence=result['confidence'],
                method=result['method']
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch match error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check cho mapping module."""
    matcher = get_drug_matcher()
    
    return {
        "status": "healthy",
        "module": "mapping_drugs",
        "cache_loaded": len(matcher.drug_cache) > 0,
        "drugs_in_cache": len(matcher.drug_cache),
        "fuzzy_enabled": len(matcher.fuzzy_names) > 0,
        "vector_enabled": matcher.vectorizer is not None
    }
