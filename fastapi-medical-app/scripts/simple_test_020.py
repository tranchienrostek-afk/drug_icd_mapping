# Simple Integration Test - No verbose logs
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app')

import asyncio
import time
import logging

# Suppress verbose logs
logging.getLogger().setLevel(logging.WARNING)

async def test_simple():
    from app.service.crawler.main import scrape_drug_web_advanced
    
    print("="*60)
    print("SIMPLE INTEGRATION TEST")
    print("="*60)
    
    drug = "Paracetamol 500mg"
    print(f"\nTesting: '{drug}'")
    
    start = time.time()
    result = await scrape_drug_web_advanced(drug, headless=True)
    elapsed = time.time() - start
    
    print(f"\n[RESULT] Time: {elapsed:.1f}s")
    
    if isinstance(result, dict):
        if result.get('status') == 'not_found':
            print(f"Status: NOT FOUND")
        else:
            print(f"Ten thuoc: {result.get('ten_thuoc', 'N/A')}")
            print(f"SDK: {result.get('so_dang_ky', 'N/A')}")
            hoat_chat = result.get('hoat_chat', 'N/A')
            if hoat_chat and len(hoat_chat) > 50:
                hoat_chat = hoat_chat[:50] + "..."
            print(f"Hoat chat: {hoat_chat}")
            print(f"Source: {result.get('source', 'N/A')}")
            
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_simple())
