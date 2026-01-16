from typing import List, Dict
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Lazy initialization to avoid import-time errors
_client = None
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

def _get_client():
    global _client
    if _client is None:
        try:
            from openai import AzureOpenAI
            _client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        except Exception as e:
            print(f"Warning: Could not init OpenAI client: {e}")
    return _client

def analyze_treatment_group(drugs_str: str, diseases_str: str, verified_links) -> dict:
    """
    Analyzes the suitability of drugs for specific diseases using LLM.
    (Restored/Refactored from original app/services.py)
    """
    system_prompt = """
    Bạn là một dược sĩ AI chuyên nghiệp. Hãy phân tích sự phù hợp của các thuốc sau đây đối với bệnh lý được cung cấp.
    Dựa trên:
    1. Kiến thức y khoa chuẩn.
    2. Danh sách liên kết đã xác minh (Verified Links) nếu có.
    
    Output JSON format:
    {
      "analysis": [
        {
          "drug": "Tên thuốc",
          "suitable": true/false (phù hợp hay không),
          "role": "main/supportive/none",
          "explanation": "Giải thích ngắn gọn"
        }
      ],
      "summary": "Tổng quan chung"
    }
    """
    
    user_prompt = f"""
    Danh sách thuốc: {drugs_str}
    Chẩn đoán bệnh: {diseases_str}
    Verified Links (Tham khảo): {json.dumps(verified_links, ensure_ascii=False)}
    
    Hãy phân tích từng thuốc.
    """
    
    client = _get_client()
    if client is None:
        return {
            "analysis": [],
            "summary": "AI service not available (OpenAI client not initialized)"
        }
    
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return {
            "analysis": [],
            "summary": f"Lỗi khi gọi AI phân tích: {str(e)}"
        }

async def analyze_treatment_group_wrapper(drug_dicts: List[Dict], disease_dicts: List[Dict]):
    """
    Async wrapper for internal use
    """
    drugs_str = ", ".join([d['ten_thuoc'] for d in drug_dicts])
    diseases_str = ", ".join([d.get('disease_name', 'Unknown') for d in disease_dicts])
    
    # Call sync function (or make it async properly)
    # For now simply calling it
    res = analyze_treatment_group(drugs_str, diseases_str, [])
    
    # Convert to expected list format if needed
    annotated_results = []
    analysis_map = {item['drug'].lower(): item for item in res.get('analysis', [])}
    
    for drug in drug_dicts:
        name = drug['ten_thuoc']
        info = analysis_map.get(name.lower(), {})
        annotated_results.append({
            "id": drug.get('id'), # preserve ID if passed
            "name": name,
            "validity": "valid" if info.get('suitable') else "warning",
            "role": info.get('role', 'unknown'),
            "explanation": info.get('explanation', 'AI could not analyze this specific drug'),
            "source": "AI_RESTORED"
        })
        
    return annotated_results
