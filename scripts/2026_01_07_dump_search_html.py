import asyncio
import sys
import os
from playwright.async_api import async_playwright

# Layout adjustments for import
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "fastapi-medical-app"))

try:
    from app.service.crawler.config import get_drug_web_config
    from app.service.crawler.core_drug import try_selectors
except ImportError:
    pass

async def dump_html():
    print("Dumping Search HTML...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        # Go to Search Page
        url = "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx"
        await page.goto(url)
        
        # Input Key
        selector = "#search-form input[name='key']"
        await page.locator(selector).fill("Symbicort 120 liều")
        await page.keyboard.press("Enter")
        
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5) # Wait for results
        
        content = await page.content()
        with open("search_result.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Saved search_result.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_html())
