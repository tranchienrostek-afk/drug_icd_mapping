import asyncio
from app.api.drugs import DrugDbEngine
from app.services import scrape_drug_web
import json

async def verify_final():
    print("--- Final Verification of Identifying Drugs ---")
    drugs_to_test = ["Paracetamol (acetaminophen) 500mg", "Cetirizin 10mg"]
    
    for drug in drugs_to_test:
        print(f"\nTesting: {drug}")
        # Mimic the flow in identify_drugs
        from app.utils import normalize_drug_name
        keyword = drug.strip()
        normalized = normalize_drug_name(keyword)
        if normalized:
             print(f"Normalized: {normalized}")
             keyword = normalized
             
        # Scrape
        result = await scrape_drug_web(keyword)
        if result:
            print(f"SUCCESS: Found {result.get('ten_thuoc')} with SDK {result.get('so_dang_ky')}")
            print(f"Source: {result.get('source')}")
            # print(f"Usage: {result.get('chi_dinh')[:100]}...")
        else:
            print(f"FAILED: Result is None for {drug}")

if __name__ == "__main__":
    asyncio.run(verify_final())
