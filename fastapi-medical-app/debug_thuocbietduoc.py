import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_tbd")

async def debug_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://thuocbietduoc.com.vn"
        keyword = "Panadol" # Likely multiple results
        
        logger.info(f"Navigating to {url}")
        await page.goto(url)
        
        # Current Search Selector from web_crawler.py
        # XPath_Input_Search: "//*[@id='search-input']"
        # HanhDong_TimKiem: "ENTER"
        
        logger.info("Searching...")
        await page.locator("//*[@id='search-input']").fill(keyword)
        await page.keyboard.press("Enter")
        
        await page.wait_for_selector("body", timeout=10000)
        await asyncio.sleep(3) # Wait for results
        
        logger.info("Capturing Search Results HTML...")
        
        # Inspect the container mentioned by user: /html/body/main/section[2]/div/div[2]
        # We'll dump the inner HTML of section[2] if possible
        try:
            content = await page.locator("body").inner_html()
            # Try to narrow down if possible, but body is safe
            # Checking user's path
            # Case 1: /html/body/main/section[2]/div/div[2]/div/div/h3/a
            # Let's verify if section[2] exists
            sections = await page.locator("//section").count()
            logger.info(f"Found {sections} sections.")
            
            # Save to file for inspection
            with open("tbd_search_dump.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Saved tbd_search_dump.html")
            
            # Print specific checks
            links_h3 = await page.locator("//h3/a").count()
            logger.info(f"Found {links_h3} links inside h3.")
             
        except Exception as e:
            logger.error(f"Error dumping: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_search())
