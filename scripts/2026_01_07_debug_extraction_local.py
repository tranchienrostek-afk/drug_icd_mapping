import asyncio
import sys
import os
import traceback

# Layout adjustments for import
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "fastapi-medical-app"))

from playwright.async_api import async_playwright
try:
    from app.service.crawler.config import get_drug_web_config
    from app.service.crawler.core_drug import scrape_single_site_drug
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def debug_symbicort():
    print("STARTED: Local Extraction Debug for 'Symbicort 120 lieu'")
    
    try:
        # 1. Config
        configs = get_drug_web_config()
        # Filter only ThuocBietDuoc
        target_config = next((c for c in configs if c['site_name'] == 'ThuocBietDuoc'), None)
        
        if not target_config:
            print("Error: ThuocBietDuoc config not found")
            return

        # 2. Launch Browser
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(
                headless=False, # VISIBLE MODE
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-extensions"
                ]
            )
            
            # 3. Scrape
            print(f"Using Config URL: {target_config['url']}")
            
            # Use lower-level calls to inspect page
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font"] else route.continue_())
            
            # Manual Navigation/Search
            await page.goto(target_config['url'])
            await page.fill("#search-form input[name='key']", "Symbicort 120 liều")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)
            
            print(f"Current URL: {page.url}")
            
            links = await page.locator("a").all()
            print(f"Found {len(links)} total links. Showing first 20 hrefs:")
            for i, link in enumerate(links[:20]):
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if href and "thuoc" in href:
                    print(f"#{i}: {text.strip()} -> {href}")
            
            # Now try core logic
            results = await scrape_single_site_drug(browser, target_config, "Symbicort 120 liều")
            
            # 4. Report
            print("\nRESULT:")
            if not results:
                print("No items found.")
            
            for idx, item in enumerate(results):
                print(f"Item #{idx+1}")
                print(f"Link: {item.get('Link')}")
                data = item.get('_extracted_data', {})
                print(f"SDK: {data.get('so_dang_ky')}")
                print(f"HoatChat: {data.get('hoat_chat')}")
                print(f"CongTy: {data.get('cong_ty_san_xuat')}")
                
            await browser.close()
            print("DONE")
            
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_symbicort())
