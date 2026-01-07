import asyncio
from playwright.async_api import async_playwright

async def run():
    url = "https://thuocbietduoc.com.vn/thuoc-53025/partamol-tab.aspx"
    print(f"Inspecting {url}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        
        try:
             # Try to find the node containing "Thành phần" (most common) or "Hoạt chất"
             loc = page.locator("xpath=//*[contains(text(), 'Thành phần')]")
             if await loc.count() == 0:
                 loc = page.locator("xpath=//*[contains(text(), 'Hoạt chất')]")

             if await loc.count() > 0:
                 print(f"Node Text: {await loc.first.inner_text()}")
                 html = await loc.first.locator('..').inner_html()
                 print(f"Parent HTML: {html[:1000]}") # 1000 chars should be enough
             else:
                 print("Not found.")

             # Also check "Số đăng ký" again to confirm parent structure compatibility
             loc2 = page.locator("xpath=//*[contains(text(), 'Số đăng ký')]")
             if await loc2.count() > 0:
                 print(f"SDK Parent HTML: {(await loc2.first.locator('..').inner_html())[:500]}")

        except Exception as e:
            print(f"Error: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
