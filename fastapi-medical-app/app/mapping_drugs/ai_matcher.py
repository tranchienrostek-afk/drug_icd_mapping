
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Check available packages
try:
    import openai
    _openai_available = True
except ImportError:
    _openai_available = False

logger = logging.getLogger("mapping_drugs.ai_matcher")
logger.info(f"[AISemanticMatcher] Module loaded. OpenAI available: {_openai_available}")


# =============================================================================
# EXPERT PROMPT - Dược sĩ AI (Generalized - No Hardcoded Drugs)
# =============================================================================

DRUG_MATCHING_SYSTEM_PROMPT = """Bạn là AI Dược sĩ Giám định Bảo hiểm.

Nhiệm vụ của bạn là SO KHỚP (MATCHING) từng Yêu cầu bồi thường (Claim)
với tối đa MỘT Hóa đơn thuốc (Medicine) phù hợp nhất,
dựa trên tư duy dược lý (semantic & clinical), KHÔNG so chuỗi cứng nhắc.

==============================
I. PIPELINE SUY LUẬN BẮT BUỘC
==============================

BƯỚC 1: PHÂN LOẠI CLAIM
- Nếu claim KHÔNG PHẢI là thuốc (dịch vụ kỹ thuật, xét nghiệm, thăm dò chức năng…)
  → KHÔNG được ghép với bất kỳ medicine nào
  → match_status = "no_match"
  → medicine_id = null
  → confidence_score ≤ 0.3
  → reasoning phải nêu rõ: "Dịch vụ y tế, không phải thuốc".

BƯỚC 2: CHUẨN HÓA NGẦM (KHÔNG TRẢ RA OUTPUT)
Chuẩn hóa cho cả claim và medicine:
- Tên thương mại (Brand)
- Hoạt chất (Active ingredient)
- Hàm lượng (Dosage)
- Dạng bào chế (Tablet, Capsule, Syrup, Solution…)

CHẤP NHẬN & ƯU TIÊN CAO:
- Brand ↔ Generic (Pantoloc ↔ Pantoprazole, Medovent ↔ Ambroxol)
- Viết hoa/thường, viết tắt, đa ngôn ngữ
- Bỏ qua nhà sản xuất (Takeda…)
- Bỏ qua quy cách đóng gói nếu hoạt chất + hàm lượng trùng

BƯỚC 3: LOGIC MATCHING (BẮT BUỘC ÁP DỤNG)
- Hoạt chất trùng + hàm lượng tương đương
  → match_status = "matched"
  → confidence_score ≥ 0.9

- Hoạt chất trùng, hàm lượng/dạng gần đúng
  → match_status = "partially_matched"
  → confidence_score 0.7 – 0.89

- Chỉ trùng tên thương mại hoặc công dụng
  → match_status = "weak_match"
  → confidence_score 0.5 – 0.69

- Không liên quan dược lý
  → match_status = "no_match"
  → confidence_score < 0.5

BƯỚC 4: CHỌN MEDICINE TỐT NHẤT
- MỖI claim BẮT BUỘC phải sinh ra ĐÚNG 1 kết quả trong mảng "matches"
- Nếu không có medicine phù hợp → medicine_id = null

==============================
II. OUTPUT FORMAT (BẮT BUỘC TUÂN THỦ)
==============================

- Chỉ trả về JSON thuần túy
- KHÔNG markdown
- KHÔNG giải thích ngoài JSON
- KHÔNG được trả về mảng matches rỗng

Cấu trúc JSON DUY NHẤT được phép trả về:

{
  "matches": [
    {
      "claim_id": "string",
      "medicine_id": "string | null",
      "claim_service": "string",
      "medicine_service": "string | null",
      "match_status": "matched" | "partially_matched" | "weak_match" | "no_match",
      "confidence_score": number,
      "reasoning": "string"
    }
  ]
}
"""

DRUG_MATCHING_USER_PROMPT = """
Dưới đây là danh sách Claims (Yêu cầu bồi thường)
và Medicines (Hóa đơn thuốc) cần so khớp.

=== CLAIMS ===
{claims_json}

=== MEDICINES ===
{medicine_json}

=== DATABASE ENRICHMENT (Optional Context) ===
{db_enrichment}

Hãy thực hiện matching cho TỪNG claim theo đúng pipeline đã mô tả.
"""

from datetime import datetime

class AISemanticMatcher:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = None
        self.client_type = None
        self.model = None
        
        # Load Env Vars
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("OPENAI_BASE_URL") or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_version = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-06-01"
        self.azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME")
        
        # Priority: Azure > Standard OpenAI
        if _openai_available:
            try:
                from openai import AsyncOpenAI, AsyncAzureOpenAI
                
                if self.azure_api_key and self.azure_endpoint:
                    # Configure for Azure
                    self.client = AsyncAzureOpenAI(
                        api_key=self.azure_api_key,
                        api_version=self.azure_version,
                        azure_endpoint=self.azure_endpoint
                    )
                    self.client_type = "azure"
                    # Default to gpt-4o-mini if not specified, as requested by user
                    self.model = model or self.azure_deployment or "gpt-4o-mini"
                    logger.info(f"[AISemanticMatcher] Initialized AsyncAzureOpenAI (deployment: {self.model})")
                    
                elif self.openai_api_key:
                    # Configure for Standard OpenAI
                    self.client = AsyncOpenAI(
                        api_key=self.openai_api_key
                    )
                    self.client_type = "openai"
                    self.model = model or "gpt-4o-mini"
                    logger.info(f"[AISemanticMatcher] Initialized AsyncOpenAI (model: {self.model})")
                
                else:
                    logger.warning("[AISemanticMatcher] No API key found (OpenAI or Azure)")
            except Exception as e:
                logger.error(f"[AISemanticMatcher] Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("[AISemanticMatcher] openai library NOT installed")

    
    async def match_claims_medicine(
        self,
        claims: List[Dict],
        medicine: List[Dict],
        db_enrichment: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        So khớp Claims với Medicine sử dụng AI (OpenAI v1 syntax).
        """
        if not self.client:
            logger.error("[AISemanticMatcher] Cannot run - Client not initialized")
            return self._fallback_response(claims, medicine)
        
        start_time = datetime.now()
        
        try:
            # Prepare prompts
            claims_json = json.dumps(claims, ensure_ascii=False, indent=2)
            medicine_json = json.dumps(medicine, ensure_ascii=False, indent=2)
            db_info = json.dumps(db_enrichment, ensure_ascii=False, indent=2) if db_enrichment else "Không có"

            user_prompt = DRUG_MATCHING_USER_PROMPT.format(
                claims_json=claims_json,
                medicine_json=medicine_json,
                db_enrichment=db_info
            )
            
            logger.info(f"[AISemanticMatcher] Calling {self.client_type} model '{self.model}'...")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": DRUG_MATCHING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.0,
                max_tokens=2000
                # timeout is configured in client or http_client if needed, default is usually sufficient
            )
            
            # Parse response
            ai_output = response.choices[0].message.content
            
            # Try to extract JSON from response
            result = self._parse_ai_response(ai_output)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result["ai_model"] = self.model
            result["processing_time_ms"] = round(processing_time, 2)
            
            logger.info(f"[AISemanticMatcher] Completed in {processing_time:.0f}ms")
            return result
            
        except Exception as e:
            print(f"\n[DEBUG] AI Error: {e}\n") # DEBUG PRINT
            return self._fallback_response(claims, medicine, error_msg=str(e))
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response to extract JSON."""
        try:
            if not response_text:
                return {"matches": [], "summary": {"error": "Empty response from AI"}}

            # Try direct JSON parse
            if response_text.strip().startswith("{"):
                return json.loads(response_text)
            
            # Try extracting from code block
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            
            if "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            
            # Fallback
            return {"matches": [], "raw_output": response_text}
            
        except Exception as e:
            logger.error(f"[AISemanticMatcher] JSON Parse Error: {e}")
            return {"matches": [], "error": str(e), "raw_output": response_text}

    def _fallback_response(self, claims: List[Dict], medicine: List[Dict], error_msg: str = None) -> Dict:
        """Return unmatched response on failure."""
        matches = []
        for c in claims:
            matches.append({
                "claim_id": c.get("id") or c.get("claim_id"), # Handle ID correctly
                "medicine_id": None,
                "match_status": "no_match",
                "confidence_score": 0.0,
                "reasoning": f"AI Matcher failed: {error_msg}" if error_msg else "AI Matcher failed or unavailable"
            })
        return {"matches": matches, "error_details": error_msg}

# Synchronous wrapper if needed (deprecated in async flow)
def ai_match_drugs_sync(claims, medicine):
    import asyncio
    matcher = AISemanticMatcher()
    return asyncio.run(matcher.match_claims_medicine(claims, medicine))
