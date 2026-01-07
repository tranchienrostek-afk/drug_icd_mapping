import asyncio
import sys
import os
from dotenv import load_dotenv

# Ensure app in path
sys.path.append('/app')

# Load env from .env in /app
load_dotenv('/app/.env')

from app.services import scrape_drug_web

async def main():
    keyword = "paracetamol" # Common drug
    print(f"Testing scraper for: {keyword}")
    result = await scrape_drug_web(keyword)
    print("Result:")
    # Print keys to verify structure
    if result:
        print(f"Keys: {result.keys()}")
        print(f"Source: {result.get('so_dang_ky')}")
        print(f"Content Length: {len(result.get('chi_dinh', ''))}")
    else:
        print("Empty result")

if __name__ == "__main__":
    asyncio.run(main())
