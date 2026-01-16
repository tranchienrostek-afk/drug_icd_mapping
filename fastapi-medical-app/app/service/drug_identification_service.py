from app.service.drug_search_service import DrugSearchService
from app.service.crawler import scrape_drug_web_advanced as scrape_drug_web
from app.core.utils import normalize_drug_name

class DrugIdentificationService:
    def __init__(self, search_service: DrugSearchService = None):
        if search_service is None:
            self.search_service = DrugSearchService()
        else:
            self.search_service = search_service

    async def process_batch(self, drug_names: list) -> list:
        results = []
        seen_sdk = {} # Check duplicates based on SDK in the current batch
        
        # Pre-process unique list to avoid duplicates in input
        input_drugs = list(dict.fromkeys(drug_names))
        
        for drug_raw in input_drugs:
            drug_data = await self.identify_drug(drug_raw)
            
            if drug_data:
                # Duplicate Logic within Batch
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
                 
        return results

    async def identify_drug(self, drug_raw: str) -> dict:
        keyword = drug_raw.strip()
        
        # 1. Normalization
        normalized = normalize_drug_name(keyword)
        if normalized:
             # print(f"Normalized: '{keyword}' -> '{normalized}'") # Optional logging
             keyword = normalized
        
        # 2. Smart DB Search
        db_result = await self.search_service.search_drug_smart(keyword)
        
        use_db = False
        if db_result:
            data = db_result.get('data', {})
            # DB Confidence Check: verified & has SDK
            if data.get('so_dang_ky') and data.get('is_verified') == 1:
                use_db = True
        
            if use_db:
                 info = db_result['data']
                 return {
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

        # 3. Web Search Fallback
        # Only search if DB didn't yield a high confidence verified result
        web_info = await scrape_drug_web(keyword)
        
        if web_info:
            info = web_info
            return {
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
        
        # If DB had a partial result but we skipped it because it wasn't verified enough, 
        # and Web failed, maybe we should return the partial DB result?
        # Current logic in original code was: "elif db_result: pass" (doing nothing), 
        # so returning None is consistent with original behavior (status: Not Found).
        
        return None
