import asyncio
from playwright.async_api import async_playwright

async def debug_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            # Try correct TBD search URL
            url = "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx"
            print(f"Opening {url}")
            await page.goto(url)
            
            # Find any input
            inputs = await page.query_selector_all("input")
            for inp in inputs:
                id_ = await inp.get_attribute("id")
                name_ = await inp.get_attribute("name")
                if id_ or name_:
                    print(f"Found Input: id='{id_}', name='{name_}'")
            
            # Try filling 'txtKeywords' or 'txtdrug'
            search_box = await page.query_selector("#txtKeywords, #txtdrug, input[type='text']")
            if search_box:
                kw = "Paracetamol"
                print(f"Filling search box with {kw}")
                await search_box.fill(kw)
                await page.keyboard.press("Enter")
                print("Waiting for results...")
                await page.wait_for_timeout(5000)
                
                print(f"URL after search: {page.url}")
                html = await page.content()
                with open("tbd_results.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("Saved results to tbd_results.html")
                
                # Check container /html/body/main/section[2]/div/div[2]/div
                container = page.locator("xpath=/html/body/main/section[2]/div/div[2]/div")
                count = await container.count()
                print(f"Items found in container: {count}")
                
            else:
                print("No search box found.")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_search())
