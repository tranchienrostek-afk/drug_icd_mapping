import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SearchTester")

async def test_search(keyword, url, input_selector, submit_selector):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print(f"\n--- Testing Keyword: '{keyword}' on {url} ---")
            await page.goto(url)
            await page.fill(input_selector, keyword)
            await page.press(input_selector, "Enter")
            await asyncio.sleep(3) # Wait for results
            
            # Simple check: look for "Không tìm thấy" or similar
            content = await page.content()
            if "không tìm thấy" in content.lower() or "0 kết quả" in content.lower():
                print("RESULT: NOT FOUND")
            else:
                print("RESULT: POTENTIAL MATCHES FOUND")
                # print(f"Title: {await page.title()}")
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

async def main():
    # Test cases
    keywords = [
        "Candesartan 16mg Hydrochlorothiazid 12.5mg", # My current clean_kw
        "Candesartan Hydrochlorothiazid",            # Simplified
        "Paracetamol 500mg"
    ]
    
    # Sites
    # TBD: https://www.thuocbietduoc.com.vn/thuoc/dr-search.aspx
    # TTT: https://trungtamthuoc.com/tim-kiem
    
    for kw in keywords:
        await test_search(kw, "https://www.thuocbietduoc.com.vn/thuoc/dr-search.aspx", "input#txtdrug", "input#txtdrug")
        await test_search(kw, "https://trungtamthuoc.com/tim-kiem", "input#search-input", "input#search-input")

if __name__ == "__main__":
    asyncio.run(main())
