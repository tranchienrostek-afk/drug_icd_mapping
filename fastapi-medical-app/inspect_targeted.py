import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # TBD
        url = "https://www.thuocbietduoc.com.vn/thuoc/dr-search.aspx"
        await page.goto(url)
        print(f"TBD URL: {page.url}")
        inputs = await page.query_selector_all("input[type='text'], input:not([type])")
        for i in inputs:
             print(f"TBD Input: id='{await i.get_attribute('id')}', name='{await i.get_attribute('name')}'")
        
        # TTT
        url = "https://trungtamthuoc.com/tim-kiem"
        await page.goto(url)
        print(f"TTT URL: {page.url}")
        inputs = await page.query_selector_all("input[type='text'], input:not([type])")
        for i in inputs:
             print(f"TTT Input: id='{await i.get_attribute('id')}', name='{await i.get_attribute('name')}'")
             
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
