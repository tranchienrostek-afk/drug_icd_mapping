"""
Agent Search Service - Rewritten based on working browser_mcp_agent solution.
Uses direct AsyncAzureOpenAI client and simple Agent Loop (Plan -> Act -> Observe).
Removed all mcp-agent dependencies.
"""
import os
import json
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AsyncOpenAI
from app.service.playwright_manager import playwright_manager
from app.service.search_normalizer import normalize_drug_name

load_dotenv()

# OpenAI Client Setup
def get_openai_client():
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        return AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        ), os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    else:
        return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")), "gpt-4o-mini"

SYSTEM_PROMPT = """
Bạn là một Browser Agent. Nhiệm vụ: tìm thông tin thuốc từ web và trả về JSON.

## Actions (Chọn 1)
1. `{"action": "navigate", "url": "..."}` - Đi đến URL mới
2. `{"action": "answer", "content": {...}}` - Trả lời với thông tin tìm được
3. `{"action": "reflect", "thought": "..."}` - Suy nghĩ (CHỈ DÙNG KHI THẬT SỰ CẦN)

## CHIẾN LƯỢC (5 rounds)

### Round 1: Tìm kiếm
Navigate đến: `https://trungtamthuoc.com/search?q=<tên_thuốc>`

### Round 2: Click vào kết quả
- Tìm trong "Valid Links" link có chứa tên thuốc (VD: trungtamthuoc.com/thuoc/...)
- Navigate đến link chi tiết đó

### Round 3+: ĐỌC DOM VÀ TRẢ ANSWER
**QUAN TRỌNG**: Sau khi vào trang chi tiết thuốc, hãy:
1. ĐỌC DOM Content - thông tin thuốc NẰM TRONG ĐÓ
2. Tìm các trường: "Số đăng ký", "Hoạt chất", "Chỉ định", "Chống chỉ định"
3. Nếu thấy thông tin -> return `{"action": "answer", "content": {...}}`

### Fallback (nếu trungtamthuoc không có):
- thuocbietduoc.com.vn, drugbank.vn, nhathuoclongchau.com.vn

## QUAN TRỌNG
- KHÔNG LẶP URL đã có trong history
- SAU KHI VÀO TRANG CHI TIẾT (URL có /thuoc/ hoặc tên thuốc) => PHẢI ĐỌC DOM VÀ TRẢ ANSWER
- Reflect CHỈ KHI không tìm thấy gì trong DOM

## Answer Format
Khi tìm thấy thông tin trong DOM, trả về:
```json
{
  "action": "answer",
  "content": {
    "official_name": "Tên thuốc chính thức",
    "sdk": "Số đăng ký (VD: VN-12345-22)",
    "active_ingredient": "Hoạt chất",
    "usage": "Chỉ định/Công dụng",
    "dosage": "Liều dùng",
    "contraindications": "Chống chỉ định",
    "source_url": "URL nguồn",
    "confidence": 0.9
  }
}
```
NẾU BẠN ĐANG Ở TRANG CHI TIẾT THUỐC VÀ DOM CONTENT CÓ THÔNG TIN => PHẢI TRẢ ANSWER, KHÔNG REFLECT!
"""

async def run_agent_search(drug_name: str) -> dict:
    """
    Runs the Browser Agent to search for drug information.
    Based on the working solution in browser_mcp_agent/app/main.py.
    """
    # Normalize drug name for search
    search_name = normalize_drug_name(drug_name)
    if not search_name:
        search_name = drug_name.split()[0] if drug_name else "unknown"  # Fallback to first word
    
    print(f"[Agent] Starting search for: {drug_name} -> Normalized: {search_name}")
    
    client, model_name = get_openai_client()
    
    # State
    memory = f"User Request: Tìm thông tin thuốc '{search_name}' (gốc: '{drug_name}')\n"
    current_url = "None"
    dom_content = "None"
    dom_links = []
    history = []
    steps_log = []
    
    # Agent Loop (Max 5 rounds)
    for round_idx in range(1, 6):
        print(f"--- Round {round_idx} ---")
        
        # Filter links to highlight matching drug detail pages
        matching_links = []
        other_links = []
        search_lower = search_name.lower()
        for link in dom_links[:50]:
            href = link.get("href", "").lower()
            text = link.get("text", "").lower()
            # Prioritize detail page links
            if search_lower in href or search_lower in text:
                if "/thuoc" in href or "/san-pham" in href or search_lower in href:
                    matching_links.append(link)
                else:
                    other_links.append(link)
        
        # Combine with matching first
        filtered_links = matching_links[:10] + other_links[:15]
        
        # Check if we're on a detail page (should extract answer)
        is_detail_page = current_url != "None" and ("/thuoc" in current_url or search_lower in current_url.lower())
        
        # Prepare Context for LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""
STATUS REPORT:
- Round: {round_idx}/5
- DRUG NAME: {search_name}
- Current URL: {current_url}
- IS DETAIL PAGE: {"YES - PHẢI ĐỌC DOM VÀ TRẢ ANSWER!" if is_detail_page else "NO"}
- Visited URLs: {history}
- MATCHING LINKS (click these first!): {json.dumps(matching_links[:5], ensure_ascii=False) if matching_links else "None"}
- Other Links: {json.dumps(other_links[:10], ensure_ascii=False) if other_links else "None"}
- DOM Content (3000 chars): {dom_content[:3000]}...

{"⚠️ BẠN ĐANG Ở TRANG CHI TIẾT THUỐC! ĐỌC DOM VÀ TRẢ ANSWER NGAY!" if is_detail_page else ""}
Return JSON only.
            """}
        ]
        
        # Call LLM
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"}
            )
            llm_output = json.loads(response.choices[0].message.content)
            action = llm_output.get("action")
            
            print(f"[Agent] Action: {action}")
            steps_log.append(f"Round {round_idx}: {action} - {json.dumps(llm_output, ensure_ascii=False)[:200]}")
            
            # Execute Action
            if action == "answer":
                result_content = llm_output.get("content", {})
                # Ensure it's a dict
                if isinstance(result_content, str):
                    try:
                        result_content = json.loads(result_content)
                    except:
                        result_content = {"raw_text": result_content}
                
                result_content["input_name"] = drug_name
                result_content["source"] = "Web Agent"
                
                return {
                    "status": "success",
                    "data": result_content,
                    "rounds": round_idx,
                    "steps": steps_log,
                    "sources": history
                }
            
            elif action == "navigate":
                target_url = llm_output.get("url", "")
                
                # Handle search query if not valid URL
                if not target_url.startswith("http"):
                    target_url = f"https://www.bing.com/search?q={target_url.replace(' ', '+')}"
                
                print(f"[Agent] Navigating to: {target_url}")
                dom_result = await playwright_manager.get_dom_content(target_url)
                
                current_url = target_url
                dom_content = dom_result.get("content", "")
                dom_links = dom_result.get("links", [])
                
                memory += f"\n[Round {round_idx}] Visited {target_url}. Title: {dom_result.get('title')}.\n"
                history.append(target_url)
                
            elif action == "reflect":
                thought = llm_output.get("thought", "")
                memory += f"\n[Round {round_idx}] Reflection: {thought}\n"
                
            else:
                memory += f"\n[Round {round_idx}] Unknown action: {action}\n"

        except Exception as e:
            print(f"[Agent] Error in Round {round_idx}: {e}")
            memory += f"\n[Error] {str(e)}\n"
            
    # Fallback if max rounds reached
    return {
        "status": "timeout",
        "message": f"Đã hết số vòng tìm kiếm tối đa (5 rounds) cho thuốc '{drug_name}'.",
        "data": {
            "input_name": drug_name,
            "official_name": None,
            "sdk": None,
            "active_ingredient": None,
            "usage": None,
            "source": "Web Agent (Timeout)",
            "confidence": 0
        },
        "steps": steps_log,
        "sources": history
    }
