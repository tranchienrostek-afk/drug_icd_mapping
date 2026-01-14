from fastapi import APIRouter, HTTPException
from app.models import DrugRequest, DrugConfirmRequest, DrugDiseaseLinkRequest, DrugStagingResponse, DrugHistoryResponse, DrugStagingUpdateRequest
from typing import List
from app.services import DrugDbEngine
from app.service.crawler import scrape_drug_web_advanced as scrape_drug_web
from app.utils import normalize_drug_name

router = APIRouter()
db = DrugDbEngine()

@router.post("/knowledge/link")
async def link_drug_knowledge(payload: DrugDiseaseLinkRequest):
    """
    API móc nối kiến thức: Thuốc (SDK) - Bệnh (ICD).
    Lưu vào bảng drug_disease_links.
    """
    result = db.link_drug_disease(payload.model_dump())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/")
async def get_all_drugs(page: int = 1, limit: int = 10, search: str = ""):
    result = db.get_all_drugs(page, limit, search)
    return result

@router.get("/{row_id}")
async def get_drug_details(row_id: int):
    result = await db.get_drug_by_id(row_id)
    if not result:
        raise HTTPException(status_code=404, detail="Drug not found")
    return result

@router.post("/confirm")
async def confirm_drug(payload: DrugConfirmRequest):
    """
    API để lưu thông tin thuốc đã kiểm chứng vào DB.
    """
    result = db.save_verified_drug(payload.model_dump())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/admin/staging", response_model=List[DrugStagingResponse])
async def get_pending_staging():
    """
    Lấy danh sách thuốc đang chờ duyệt (Staging).
    """
    results = db.get_pending_stagings()
    return results

@router.post("/admin/approve/{staging_id}")
async def approve_drug_staging(staging_id: int, user: str = "admin"):
    """
    Duyệt thuốc từ Staging -> Main Table (có lưu History nếu ghi đè).
    """
    result = db.approve_staging(staging_id, user)
    if result["status"] == "error":
         raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/admin/reject/{staging_id}")
async def reject_drug_staging(staging_id: int):
    """
    Từ chối thuốc từ Staging -> Di chuyển sang bảng lịch sử (Soft Reject).
    """
    result = db.reject_staging(staging_id)
    if result["status"] == "error":
         raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.put("/admin/staging/{staging_id}")
async def update_drug_staging(staging_id: int, payload: DrugStagingUpdateRequest):
    """
    Chỉnh sửa thông tin thuốc trong Staging.
    """
    result = db.update_staging(staging_id, payload.model_dump())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/admin/staging/clear")
async def clear_all_staging_items():
    """
    Xóa toàn bộ Staging pending -> Move all to history (nhà kho).
    """
    result = db.clear_all_staging()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/identify")
async def identify_drugs(payload: DrugRequest):
    results = []
    seen_sdk = {} # Để check trùng lặp thuốc dựa trên SĐK
    
    # Pre-process unique list to avoid duplicates
    input_drugs = list(dict.fromkeys(payload.drugs))
    
    for drug_raw in input_drugs:
        drug_data = None
        keyword = drug_raw.strip()
        
        # --- NEW: Normalization ---
        normalized = normalize_drug_name(keyword)
        if normalized:
             print(f"Normalized: '{keyword}' -> '{normalized}'")
             keyword = normalized # Use normalized name for search
        # --------------------------
        
        # 1. Start with Smart DB Search
        db_result = await db.search_drug_smart(keyword)
        
        # Logic to decide if we stop or go to Web
        # User defined levels:
        # 100% (Exact) -> Stop
        # 95% (Partial) -> Stop? User said "Verified -> 95%". If verified & has SDK, usually good enough.
        # 90% (Vector) -> Stop if verified.
        # User said: "If verified with SDK -> Select... If not verified -> Search Web"
        
        use_db = False
        if db_result:
            conf = db_result.get('confidence', 0)
            data = db_result.get('data', {})
            # Check verified status just to be fastidious (DB logic already filters verified=1 but let's be safe)
            if data.get('so_dang_ky') and data.get('is_verified') == 1:
                use_db = True
        
            if use_db:
                 info = db_result['data']
                 drug_data = {
                    "input_name": drug_raw,
                    "official_name": info.get('ten_thuoc'),
                    "sdk": info.get('so_dang_ky'),
                    "active_ingredient": info.get('hoat_chat'),
                    "usage": info.get('chi_dinh', 'N/A'),
                    "classification": info.get('classification'),
                    "note": info.get('note'),
                    "source": db_result.get('source'),
                    "confidence": db_result.get('confidence'),
                    "source_urls": [] # Database source
                }
            else:
                # 2. Web Search Fallback
                # Only search if DB didn't yield a high confidence verified result
                web_info = await scrape_drug_web(keyword)
                
                if web_info:
                    info = web_info
                    drug_data = {
                        "input_name": drug_raw,
                        "official_name": info.get('ten_thuoc'),
                        "sdk": info.get('so_dang_ky'),
                        "active_ingredient": info.get('hoat_chat'),
                        "usage": info.get('chi_dinh', 'N/A'),
                        "contraindications": info.get('chong_chi_dinh'),
                        "dosage": info.get('lieu_dung'),
                        "source": info.get('source', "Web"),
                        "confidence": info.get('confidence', 0.8),
                        "source_urls": info.get('source_urls', [])
                    }
                elif db_result:
                     # Web failed, but we had a partial DB match?
                     pass
        
        if drug_data:
            # Logic check trùng trong batch hiện tại
            sdk = drug_data.get('sdk')
            if sdk and sdk not in ['N/A', 'Web Result (No SDK)']:
                if sdk in seen_sdk:
                    drug_data["is_duplicate"] = True
                    drug_data["duplicate_of"] = seen_sdk[sdk]
                else:
                    drug_data["is_duplicate"] = False
                    seen_sdk[sdk] = drug_raw
            else:
                 drug_data["is_duplicate"] = False
            
            results.append(drug_data)
        else:
             results.append({"input_name": drug_raw, "status": "Not Found"})
             
    return {"results": results}

from app.service.agent_search_service import run_agent_search

@router.post("/agent-search")
async def search_drug_agent(payload: DrugRequest):
    """
    Kích hoạt AI Agent (Browser) để tìm kiếm thuốc.
    Input: Danh sách thuốc - mỗi thuốc được search tối đa 5 rounds.
    """
    if not payload.drugs:
        raise HTTPException(status_code=400, detail="No drug name provided")
    
    results = []
    for drug_name in payload.drugs:
        result = await run_agent_search(drug_name)
        results.append(result)
    
    return {"results": results}