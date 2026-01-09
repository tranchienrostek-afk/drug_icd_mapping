# Full Integration Test - Web Crawler with Multi-Engine Fallback
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app')

import asyncio
import time
import json

async def test_full_integration():
    from app.service.crawler.main import scrape_drug_web_advanced
    
    test_drugs = [
        "Hightamine",  # Khó tìm - test fallback
        "Symbicort",   # Thuốc phổ biến
    ]
    
    print("="*60)
    print("FULL INTEGRATION TEST - Web Crawler + Multi-Engine")
    print("="*60)
    
    for drug_name in test_drugs:
        print(f"\n{'='*60}")
        print(f"Testing: '{drug_name}'")
        print("="*60)
        
        start = time.time()
        
        try:
            result = await scrape_drug_web_advanced(drug_name, headless=True)
            elapsed = time.time() - start
            
            print(f"\nResult in {elapsed:.1f}s:")
            
            if isinstance(result, dict):
                if result.get('status') == 'not_found':
                    print(f"  Status: NOT FOUND")
                    print(f"  Message: {result.get('message')}")
                else:
                    print(f"  Ten thuoc: {result.get('ten_thuoc', 'N/A')}")
                    print(f"  SDK: {result.get('so_dang_ky', 'N/A')}")
                    print(f"  Hoat chat: {result.get('hoat_chat', 'N/A')[:80] if result.get('hoat_chat') else 'N/A'}...")
                    print(f"  Source: {result.get('source', 'N/A')}")
                    print(f"  Source URLs: {result.get('source_urls', [])[:2]}")
            else:
                print(f"  Raw result: {str(result)[:200]}...")
                
        except Exception as e:
            elapsed = time.time() - start
            print(f"\n  ERROR in {elapsed:.1f}s: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("INTEGRATION TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_full_integration())
