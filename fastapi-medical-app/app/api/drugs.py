from fastapi import APIRouter, HTTPException
from app.models import DrugRequest, DrugConfirmRequest, DrugDiseaseLinkRequest, DrugStagingResponse, DrugHistoryResponse, DrugStagingUpdateRequest
from typing import List
from app.services import DrugDbEngine
from app.service.drug_identification_service import DrugIdentificationService
# from app.service.crawler import scrape_drug_web_advanced as scrape_drug_web # Moved to Service
# from app.core.utils import normalize_drug_name # Moved to Service

router = APIRouter()
db = DrugDbEngine()
identification_service = DrugIdentificationService(search_service=db.search_service) # Reuse search service from DB engine

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
    """
    Nhận dạng thuốc:
    1. Chuẩn hóa tên thuốc.
    2. Tìm trong DB (Smart Search).
    3. Nếu không có hoặc chưa verified -> Tìm Web.
    """
    results = await identification_service.process_batch(payload.drugs)
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
