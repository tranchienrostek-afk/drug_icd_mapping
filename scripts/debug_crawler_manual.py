import asyncio
import sys
import os
import json

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'fastapi-medical-app'))

from app.service.crawler import scrape_drug_web_advanced

async def run():
    keyword = "Paracetamol 500mg"
    print(f"DEBUG: Searching for '{keyword}'...")
    result = await scrape_drug_web_advanced(keyword)
    print("DEBUG: Saving result...")
    with open('scripts/debug_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("DEBUG: Done.")

if __name__ == "__main__":
    asyncio.run(run())
