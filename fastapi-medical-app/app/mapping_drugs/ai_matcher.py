
import os
import logging
import json
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

DRUG_MATCHING_SYSTEM_PROMPT = """Bạn là AI Dược sĩ Chuyên gia. Nhiệm vụ của bạn là so khớp (matching) danh sách Yêu cầu bồi thường (Claims) với danh sách Hóa đơn thuốc (Medicine).

### MATCHING RULES (QUAN TRỌNG):
1. **Semantic Matching (Linh hoạt - Relaxed)**:
   - Hãy match linh hoạt dựa trên bản chất dược lý, KHÔNG KHỚP cứng nhắc theo chuỗi ký tự.
   - CHẤP NHẬN các cặp từ đồng nghĩa (Synonyms) đa ngôn ngữ phổ biến trong y tế:
     - "Gargle" <=> "Súc họng" / "Nước súc miệng"
     - "Syrup" / "Syr" <=> "Siro"
     - "Tablet" / "Tab" <=> "Viên" / "Viên nén"
     - "Solution" / "Sol" <=> "Dung dịch"
     - "Ointment" <=> "Thuốc mỡ"
   - Nếu tên thuốc khác nhau nhưng bản chất là một (cùng hoạt chất, cùng dạng bào chế, cùng công dụng), hãy đánh giá là `matched` (hoặc `weak_match` nếu cần kiểm tra thêm).

2. **Confidence Score**:
   - 1.0: Chính xác hoàn toàn.
   - 0.9 - 0.99: Khớp rất cao (khác biệt nhỏ chính tả/format).
   - 0.7 - 0.89: Semantic match (đồng nghĩa, dịch thuật, tên thương mại khác nhưng cùng hoạt chất).
   - < 0.5: Không khớp.

3. **Output Format**:
   - Trả về JSON thuần túy (không markdown).
   - Cấu trúc bắt buộc:
     {
       "matches": [
         {
           "claim_id": "...",
           "medicine_id": "...",
           "claim_service": "...",
           "medicine_service": "...",
           "match_status": "matched" | "partially_matched" | "weak_match" | "no_match",
           "confidence_score": 0.0 - 1.0,
           "reasoning": "Giải thích ngắn gọn tại sao match"
         }
       ]
     }
"""

DRUG_MATCHING_USER_PROMPT = """
Dưới đây là danh sách Claims và Medicine cần so khớp:

### 1. Claims (Yêu cầu bồi thường)
{claims_json}

### 2. Medicine (Hóa đơn mua thuốc)
{medicine_json}

### 3. Thông tin bổ sung từ Database (Context)
{db_enrichment}

Hãy thực hiện matching từng claim với medicine phù hợp nhất.
Nếu không tìm thấy medicine phù hợp, hãy đánh dấu match_status="no_match" và medicine_id=null.
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
        
        # Prepare prompts
        claims_json = json.dumps(claims, ensure_ascii=False, indent=2)
        medicine_json = json.dumps(medicine, ensure_ascii=False, indent=2)
        db_info = json.dumps(db_enrichment, ensure_ascii=False, indent=2) if db_enrichment else "Không có"
        
        user_prompt = DRUG_MATCHING_USER_PROMPT.format(
            claims_json=claims_json,
            medicine_json=medicine_json,
            db_enrichment=db_info
        )
        
        try:
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
            logger.error(f"[AISemanticMatcher] Error calling AI: {e}")
            return self._fallback_response(claims, medicine)
    
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

    def _fallback_response(self, claims, medicine) -> Dict:
        """Return unmatched response on failure."""
        matches = []
        for c in claims:
            matches.append({
                "claim_id": c.get("claim_id"),
                "medicine_id": None,
                "match_status": "no_match",
                "confidence_score": 0.0,
                "reasoning": "AI Matcher failed or unavailable"
            })
        return {"matches": matches}

# Synchronous wrapper if needed (deprecated in async flow)
def ai_match_drugs_sync(claims, medicine):
    import asyncio
    matcher = AISemanticMatcher()
    return asyncio.run(matcher.match_claims_medicine(claims, medicine))
