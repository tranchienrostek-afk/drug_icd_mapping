import asyncio
from playwright.async_api import async_playwright

async def debug_ttt():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            url = "https://trungtamthuoc.com/tim-kiem?q=Cetirizin+10mg"
            print(f"Opening {url}")
            await page.goto(url)
            await page.wait_for_timeout(5000)
            
            print(f"Page Title: {await page.title()}")
            
            # Find any div with 'product' or similar classes
            # In TTT, results are often in divs with class 'pro-item'
            print("Searching for product items...")
            items = await page.query_selector_all("div.pro-item, div.product-item, .pro-category-item")
            for i, item in enumerate(items[:5]):
                 html = await item.inner_html()
                 print(f"Item [{i}] HTML Snippet: {html[:100]}...")
            
            # Check for current container in config: //*[@id='cscontentdetail']/div
            container_xp = "//*[@id='cscontentdetail']/div"
            cont_items = page.locator(f"xpath={container_xp}")
            print(f"Items found with current container XP: {await cont_items.count()}")
            
            await page.screenshot(path="debug_ttt.png")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_ttt())
