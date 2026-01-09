# Live test for Multi-Engine Search
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app')

import asyncio
import time

async def test_multi_engine_search():
    from playwright.async_api import async_playwright
    from app.service.crawler.search_engines import search_drug_links
    from app.service.crawler.stealth_config import BROWSER_ARGS
    
    test_drugs = [
        "Paracetamol 500mg",
        "Berodual 200",
    ]
    
    print("="*60)
    print("MULTI-ENGINE SEARCH LIVE TEST")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=BROWSER_ARGS
        )
        
        try:
            for drug_name in test_drugs:
                print(f"\n--- Testing: '{drug_name}' ---")
                start = time.time()
                
                result = await search_drug_links(
                    browser,
                    drug_name,
                    max_links=5,
                    query_variants=[f"{drug_name} thuoc", drug_name]
                )
                
                elapsed = time.time() - start
                
                print(f"  Success: {result.get('success')}")
                print(f"  Time: {elapsed:.1f}s")
                print(f"  Engines: {result.get('engines_used')}")
                print(f"  Links found: {len(result.get('links', []))}")
                
                for i, link in enumerate(result.get("links", [])[:3], 1):
                    print(f"    {i}. {link[:65]}...")
                    
        finally:
            await browser.close()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_multi_engine_search())
