import asyncio
import time
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fastapi-medical-app')))

from playwright.async_api import async_playwright
from app.service.crawler.config import get_drug_web_config
from app.service.crawler.core_drug import scrape_single_site_drug
from app.service.crawler.utils import logger

# Setup Logger for file output
import logging
file_handler = logging.FileHandler("report_ludox_test.log", mode='w', encoding='utf-8')
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

async def run_test():
    search_keyword = "Ludox - 200mg"
    print(f"--- START TEST: {search_keyword} on TrungTamThuoc ---")
    
    configs = get_drug_web_config()
    target_config = next((c for c in configs if c['site_name'] == 'TrungTamThuoc'), None)
    
    if not target_config:
        print("Error: TrungTamThuoc config not found")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-gpu', '--no-sandbox']
        )
        try:
            results = await scrape_single_site_drug(browser, target_config, search_keyword)
            
            print(f"Results Found: {len(results)}")
            for idx, item in enumerate(results):
                print(f"[{idx+1}] {item.get('ten_thuoc', 'No Name')} - SDK: {item.get('so_dang_ky', 'N/A')}")
                print(f"    Link: {item.get('Link')}")
                print(f"    Content Preview: {item.get('Content', '')[:100]}...")
            
            if not results:
                print("No results found. Checking logs for details.")
                
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            await browser.close()
    
    print("--- END TEST ---")

if __name__ == "__main__":
    asyncio.run(run_test())
