import asyncio
from app.services import scrape_drug_web
from app.utils import normalize_drug_name

async def verify_compound():
    drug = "Candesartan + hydrochlorothiazid 16mg + 12.5mg"
    print(f"\nFinal Testing Compound: {drug}")
    norm = normalize_drug_name(drug)
    print(f"Normalized: {norm}")
    
    result = await scrape_drug_web(norm)
    if result:
        print(f"SUCCESS: Found {result.get('ten_thuoc')} with SDK {result.get('so_dang_ky')}")
        print(f"Hoạt chất: {result.get('hoat_chat')}")
    else:
        print(f"FAILED: Result is None")

if __name__ == "__main__":
    asyncio.run(verify_compound())
