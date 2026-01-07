import asyncio
from playwright.async_api import async_playwright

async def find_selectors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        sites = [
            ("TBD", "https://www.thuocbietduoc.com.vn/thuoc/dr-search.aspx"),
            ("TTT", "https://trungtamthuoc.com/tim-kiem")
        ]
        
        for name, url in sites:
            print(f"\n--- Site: {name} ({url}) ---")
            try:
                await page.goto(url, timeout=30000)
                inputs = await page.locator("input").all()
                for i, inp in enumerate(inputs):
                    id_ = await inp.get_attribute("id")
                    name_ = await inp.get_attribute("name")
                    placeholder = await inp.get_attribute("placeholder")
                    print(f"[{i}] id='{id_}', name='{name_}', placeholder='{placeholder}'")
            except Exception as e:
                print(f"Error on {name}: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_selectors())
