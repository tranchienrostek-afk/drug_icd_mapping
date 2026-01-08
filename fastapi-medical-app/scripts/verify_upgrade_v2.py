import asyncio
import sys
import os
import json

# Add app directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.service.crawler.main import scrape_drug_web_advanced

async def test_search():
    keyword = "Augmentin"
    print(f"DEBUG: Searching for {keyword}...")
    
    try:
        result = await scrape_drug_web_advanced(keyword, headless=True)
        
        output_file = "verify_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"DEBUG: Results saved to {output_file}")
    except Exception as e:
        print(f"DEBUG: CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
