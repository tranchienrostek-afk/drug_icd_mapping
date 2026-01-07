"""Debug script to test drug search functionality"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.service.web_crawler import scrape_drug_web_advanced

# Test drugs from user input
TEST_DRUGS = [
    "Candesartan + hydrochlorothiazid 16mg + 12.5mg",
    "Cetirizin 10mg",
    "Rotundin 60mg",
    "Paracetamol (acetaminophen) 500mg"
]

async def main():
    print("=" * 60)
    print("DEBUG DRUG SEARCH")
    print("=" * 60)
    
    for drug in TEST_DRUGS:
        print(f"\n{'='*60}")
        print(f"🔍 Testing: {drug}")
        print("=" * 60)
        
        try:
            result = await scrape_drug_web_advanced(drug)
            
            if isinstance(result, dict):
                if result.get("status") == "not_found":
                    print(f"❌ NOT FOUND: {result.get('message')}")
                else:
                    print(f"✅ FOUND:")
                    print(f"   Tên thuốc: {result.get('ten_thuoc', 'N/A')}")
                    print(f"   Số ĐK: {result.get('so_dang_ky', 'N/A')}")
                    print(f"   Hoạt chất: {result.get('hoat_chat', 'N/A')[:100]}...")
                    print(f"   Chỉ định: {str(result.get('chi_dinh', 'N/A'))[:100]}...")
                    print(f"   Sources: {result.get('source_urls', [])}")
            else:
                print(f"⚠️ Unexpected result type: {type(result)}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
