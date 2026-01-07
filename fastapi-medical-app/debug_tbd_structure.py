import asyncio
from playwright.async_api import async_playwright

async def debug_tbd():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            url = "https://www.thuocbietduoc.com.vn/thuoc/dr-search.aspx"
            print(f"Opening {url}")
            await page.goto(url)
            await page.fill("#txtKeywords", "Paracetamol")
            await page.press("#txtKeywords", "Enter")
            await page.wait_for_timeout(5000)
            
            print(f"Page Title: {await page.title()}")
            # Check for container
            xpath_container = "/html/body/main/section[2]/div/div[2]/div"
            items = page.locator(f"xpath={xpath_container}")
            count = await items.count()
            print(f"Found {count} items for container '{xpath_container}'")
            
            if count > 0:
                # Check first link
                link_xp = ".//h3/a"
                link = items.first.locator(f"xpath={link_xp}")
                if await link.count() > 0:
                     print(f"Link HTML: {await link.first.inner_html()}")
                     print(f"Link Href: {await link.first.get_attribute('href')}")
            
            # If not found, dump some content
            if count == 0:
                 print("Container not found. Dumping main content...")
                 print(await page.inner_text("body"))
                 
            await page.screenshot(path="debug_tbd.png")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_tbd())
