import asyncio
from app.service.web_crawler import scrape_drug_web_advanced
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)

async def test_advanced_crawler():
    keyword = "Panadol"
    print(f"Testing Advanced Crawler for: {keyword}")
    
    result = await scrape_drug_web_advanced(keyword)
    
    print("\nFINAL RESULT:")
    print(f"Name: {result.get('ten_thuoc')}")
    print(f"SDK: {result.get('so_dang_ky')}")
    print(f"Active Ingredient: {result.get('hoat_chat')}")
    print(f"Company: {result.get('cong_ty_san_xuat')}")
    print(f"Classification (Dang Bao Che): {result.get('classification')}")
    print(f"Note (Nhom/Ham Luong): {result.get('note')}")
    print(f"Chi Dinh Snippet: {result.get('chi_dinh')[:200]}...")
    print(f"Source: {result.get('source')}")

if __name__ == "__main__":
    asyncio.run(test_advanced_crawler())
