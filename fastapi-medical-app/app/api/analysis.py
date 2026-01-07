from fastapi import APIRouter
from app.models import AnalysisRequest
from app.api.drugs import identify_drugs
from app.api.diseases import lookup_diseases
from app.services import analyze_treatment_group, DrugDbEngine
from app.models import DrugRequest, DiseaseRequest

router = APIRouter()
db = DrugDbEngine()

@router.post("/treatment-analysis")
async def analyze_treatment(payload: AnalysisRequest):
    # 1. Gọi API xử lý thuốc
    drug_payload = DrugRequest(drugs=payload.drugs)
    drugs_res = await identify_drugs(drug_payload)
    
    # 2. Gọi API xử lý bệnh
    disease_payload = DiseaseRequest(diagnosis=payload.diagnosis)
    diseases_res = await lookup_diseases(disease_payload)
    
    # 3. Tổng hợp thông tin để gửi cho LLM
    # User requested to include "Not Found" drugs for AI inference
    drugs_clean = drugs_res['results'] 
    diseases_clean = [d for d in diseases_res['results'] if d.get('status') != 'Not Found']
    
    # 3b. Lấy thông tin Verified Knowledge Base
    sdks = [d.get('sdk') for d in drugs_clean if d.get('sdk')]
    icds = [d.get('icd_code') for d in diseases_clean if d.get('icd_code')]
    verified_links = db.check_knowledge_base(list(sdks), list(icds))
    
    # 4. Gọi LLM phân tích (kèm verified links)
    analysis_result = analyze_treatment_group(str(drugs_clean), str(diseases_clean), verified_links)
    
    return {
        "drugs_info": drugs_res['results'],
        "diseases_info": diseases_res['results'],
        "ai_analysis": analysis_result
    }