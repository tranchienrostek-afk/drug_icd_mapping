"""
AI Semantic Matching Service - Level 6 Final Fallback
======================================================
Khi tất cả các phương pháp statistical/lexical fail,
AI sẽ là "chuyên gia dược" cuối cùng để hiểu ngữ nghĩa.

Ví dụ mà AI có thể match nhưng fuzzy/BM25 không:
- "Augmentin" ↔ "Amoxicillin + Clavulanic Acid" (cùng thuốc, khác tên)
- "Hapacol" ↔ "Paracetamol" (brand vs generic)
- "Men tiêu hóa" ↔ "Probiotic" (Việt vs Latin)
- "Thuốc ho thảo dược" ↔ "Siro Prospan" (generic description vs brand)
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("mapping_drugs.ai_matcher")

# Try to import OpenAI
_openai_available = False
try:
    import openai
    _openai_available = True
except ImportError:
    pass

logger.info(f"[AISemanticMatcher] Module loaded. OpenAI available: {_openai_available}")


# =============================================================================
# EXPERT PROMPT - Dược sĩ AI (Generalized - No Hardcoded Drugs)
# =============================================================================

DRUG_MATCHING_SYSTEM_PROMPT = """Bạn là AI Dược sĩ Chuyên gia với kiến thức sâu rộng về Dược phẩm toàn cầu và Việt Nam.

🎯 NHIỆM VỤ:
So khớp (matching) giữa hai danh sách thuốc:
- **Claims**: Thuốc khách hàng yêu cầu bồi thường bảo hiểm
- **Medicine**: Thuốc khách hàng thực tế đã mua (hóa đơn)

🧠 PHƯƠNG PHÁP SUY LUẬN:
Với mỗi cặp thuốc, hãy phân tích theo các chiều sau:

1. **Hoạt chất (Active Ingredient)**
   - Một thuốc có thể có nhiều tên thương mại khác nhau
   - Tên thương mại (brand) thường khác hoàn toàn tên hoạt chất (generic)
   - Dựa vào kiến thức dược lý để xác định hoạt chất từ tên thuốc

2. **Nhóm dược lý (Pharmacological Class)**
   - Thuốc cùng nhóm có thể được mô tả bằng các thuật ngữ khác nhau
   - Ví dụ: "men vi sinh" và "probiotic" cùng là chế phẩm lợi khuẩn

3. **Hàm lượng & Dạng bào chế**
   - Chuẩn hóa đơn vị: mg, g, ml, viên, ống...
   - 500mg = 0.5g, 1g = 1000mg

4. **Ngôn ngữ & Viết tắt**
   - Tên tiếng Việt ↔ Tên Latin/Anh
   - Viết tắt phổ biến trong y tế
   - Mô tả chung vs Tên cụ thể

5. **Công dụng điều trị (Therapeutic Use)**
   - "Thuốc ho" có thể match với bất kỳ thuốc trị ho nào
   - "Thuốc đau đầu" có thể là nhóm giảm đau

⚖️ CHIẾN LƯỢC MATCH:
- **EXACT**: Cùng tên, cùng hàm lượng → confidence 0.95-1.0
- **EQUIVALENT**: Khác tên nhưng cùng hoạt chất, cùng hàm lượng → confidence 0.85-0.95
- **SIMILAR**: Cùng nhóm thuốc, công dụng tương đương → confidence 0.70-0.85
- **POSSIBLE**: Có thể liên quan nhưng cần xác nhận → confidence 0.50-0.70
- **NO_MATCH**: Không có bằng chứng liên quan → confidence < 0.50

⚠️ QUY TẮC BẮT BUỘC:
1. **SỬ DỤNG KIẾN THỨC DƯỢC**: Dựa vào kiến thức dược lý của bạn, KHÔNG đoán mò
2. **GIẢI THÍCH LOGIC**: Mỗi match phải có reasoning rõ ràng
3. **THỪA NHẬN GIỚI HẠN**: Nếu không chắc → trả về "uncertain"
4. **KHÔNG TỰ BỊA**: Không tạo thông tin không có căn cứ

📤 OUTPUT FORMAT (JSON):
{
  "matches": [
    {
      "claim_id": "string",
      "claim_service": "string", 
      "medicine_id": "string | null",
      "medicine_service": "string | null",
      "match_status": "matched | partial_match | weak_match | no_match | uncertain",
      "confidence_score": 0.0-1.0,
      "reasoning": "Giải thích ngắn gọn: [hoạt chất/nhóm thuốc] + [lý do match/không match]"
    }
  ],
  "summary": {
    "total_processed": number,
    "matched": number,
    "partial": number,
    "unmatched": number,
    "uncertain": number
  }
}

⛔ CẢNH BÁO NGHIÊM TRỌNG:
- KHÔNG dùng từ "rejected" - thay bằng "flagged_for_review"
- AI CHỈ ĐỀ XUẤT, quyết định cuối cùng thuộc về con người
- Với case khó/mơ hồ → đánh dấu "uncertain" để human review"""


DRUG_MATCHING_USER_PROMPT = """Hãy so khớp danh sách Claims với danh sách Medicine dưới đây.

📋 DANH SÁCH CLAIMS (Yêu cầu bồi thường):
{claims_json}

💊 DANH SÁCH MEDICINE (Hóa đơn mua thuốc):
{medicine_json}

📊 THÔNG TIN BỔ SUNG TỪ DATABASE (nếu có):
{db_enrichment}

Hãy phân tích và trả về JSON output theo format đã quy định."""


class AISemanticMatcher:
    """
    AI-powered semantic drug matching.
    
    Sử dụng LLM (OpenAI GPT-4 hoặc tương đương) để match
    các thuốc mà fuzzy/BM25/TF-IDF không thể match được.
    Updated for OpenAI v1.x client.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """
        Khởi tạo AI Matcher with V1 Client.
        Support cả Standard OpenAI và Azure OpenAI.
        """
        self.client = None
        self.client_type = "unknown"
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
            
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find JSON object in text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            logger.warning("[AISemanticMatcher] Could not parse JSON from response")
            return {"matches": [], "summary": {"error": "Could not parse AI response"}}
            
        except json.JSONDecodeError as e:
            logger.error(f"[AISemanticMatcher] JSON parse error: {e}")
            return {"matches": [], "summary": {"error": str(e)}}
    
    def _fallback_response(self, claims: List[Dict], medicine: List[Dict]) -> Dict:
        """Fallback response when AI is not available."""
        return {
            "matches": [
                {
                    "claim_id": c.get("claim_id", ""),
                    "claim_service": c.get("service", ""),
                    "medicine_id": None,
                    "medicine_service": None,
                    "match_status": "uncertain",
                    "confidence_score": 0.0,
                    "reasoning": "AI không khả dụng - cần human review"
                }
                for c in claims
            ],
            "summary": {
                "total_processed": len(claims),
                "matched": 0,
                "partial": 0,
                "unmatched": 0,
                "uncertain": len(claims)
            },
            "ai_model": "fallback",
            "processing_time_ms": 0
        }


# =============================================================================
# Simplified sync version (for integration with existing service)
# =============================================================================

def ai_match_drugs_sync(
    claims: List[Dict],
    medicine: List[Dict],
    db_enrichment: Optional[Dict] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for AI matching.
    
    Use this in existing sync code.
    """
    import asyncio
    
    matcher = AISemanticMatcher(api_key=api_key)
    
    # Run async function in sync context
    return asyncio.run(
        matcher.match_claims_medicine(claims, medicine, db_enrichment)
    )
