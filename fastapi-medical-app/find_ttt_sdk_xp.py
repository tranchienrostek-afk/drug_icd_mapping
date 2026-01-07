import asyncio
from playwright.async_api import async_playwright

async def find_sdk_xp():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            url = "https://trungtamthuoc.com/thuoc-cetirizin-10mg-vacopharm"
            print(f"Opening {url}")
            await page.goto(url)
            await page.wait_for_timeout(3000)
            
            # Find element containing "Số đăng ký"
            el = await page.query_selector("text='Số đăng ký'")
            if el:
                 print(f"Found element with text 'Số đăng ký'")
                 # Get parent or sibling that contains the actual value
                 parent = await el.query_selector("xpath=..")
                 print(f"Parent Text: {await parent.inner_text()}")
                 
            # Try to find common ID/Class for SDK
            # Often it's in a list
            items = await page.query_selector_all("div.product-info-item, .info-row")
            for i in items:
                 text = await i.inner_text()
                 if "số đăng ký" in text.lower():
                      print(f"Found Info Row: {text}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(find_sdk_xp())
