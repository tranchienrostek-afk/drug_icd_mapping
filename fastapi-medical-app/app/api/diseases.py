from fastapi import APIRouter
from app.models import DiseaseRequest
from app.services import DiseaseDbEngine, scrape_icd_web

router = APIRouter()
db = DiseaseDbEngine()

@router.get("/")
async def get_diseases(page: int = 1, limit: int = 20, search: str = ""):
    """
    Get list of diseases with pagination and search.
    """
    return db.get_diseases_list(page, limit, search)

@router.post("/lookup")
async def lookup_diseases(payload: DiseaseRequest):
    results = []
    
    for diag in payload.diagnosis:
        info = db.search(diag.name, diag.icd10)
        source = "Database"
        
        if not info:
             # Nếu không tìm thấy thì tìm Web
             # info = await scrape_icd_web(diag.icd10) # Cần implement
             source = "Web"
        
        if info:
            data = info.get('data', {})
            results.append({
                "input_diagnosis": diag.name,
                "icd10_input": diag.icd10,
                "official_name": data.get('disease_name'),
                "icd_code": data.get('icd_code'),
                "chapter": data.get('chapter_name'),
                "source": info.get('source', source)
            })
        else:
             results.append({"input_diagnosis": diag.name, "status": "Not Found"})
             
    return {"results": results}