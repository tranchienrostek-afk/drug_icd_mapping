import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

# From knowledge/trungtamthuoc_extract.py
async def extract_table_field_safe(page, label: str):
    xpath = f"//tr[td[contains(normalize-space(), '{label}')]]/td[last()]"
    try:
        locator = page.locator(xpath).first
        # Lower timeout for check
        if await locator.is_visible(timeout=2000):
            text = await locator.text_content()
            return text.strip() if text else None
    except:
        pass
    return None

async def extract_section_safe(page, keyword: str):
     xpath = f"//h2[contains(normalize-space(), '{keyword}')]/following-sibling::*[preceding-sibling::h2[1][contains(normalize-space(), '{keyword}')]]"
     contents = []
     try:
         nodes = page.locator(xpath)
         count = await nodes.count()
         for i in range(count):
             try:
                 text = await nodes.nth(i).inner_text()
                 if text.strip():
                     contents.append(text.strip())
             except: continue
     except: pass
     return contents

# Main Script
async def run():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = r"C:\Users\Admin\Desktop\drug_icd_mapping\tests\result_tests"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(output_dir, f"{timestamp}_result_hightamine.json")
    
    print(f"Timestamp: {timestamp}")
    print(f"Goal: Search 'Hightamine' and extract exact info using robustness from knowledge base.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        results = {
            "search_term": "Hightamine",
            "found": False,
            "details": {},
            "error": None
        }

        try:
            # 1. Goto Homepage
            # knowledge/trungtamthuoc_search.py suggests generic selectors are safer
            await page.goto("https://trungtamthuoc.com/", timeout=60000)
            
            # 2. Search
            # Try specific ID then fallback
            search_input = page.locator("#txtKeywords")
            if await search_input.count() == 0:
                 search_input = page.locator("input[name='txtKeywords']")
            
            if await search_input.count() > 0:
                await search_input.first.fill("Hightamine")
                # knowledge suggests Enter is usually enough
                await search_input.first.press("Enter")
                print("Search submitted")
                await page.wait_for_timeout(3000) # Wait for reload
            else:
                raise Exception("Search input not found")

            # 3. Find Link
            # knowledge/trungtamthuoc_search.py uses .cs-item-product
            items = page.locator(".cs-item-product a")
            
            target_url = None
            count = await items.count()
            print(f"Items found: {count}")
            
            for i in range(count):
                try:
                    txt = await items.nth(i).inner_text()
                    href = await items.nth(i).get_attribute("href")
                    print(f"Candidate: {txt} -> {href}")
                    if "Hightamine" in txt or "hightamine" in txt.lower():
                        target_url = href
                        if not target_url.startswith("http"):
                            target_url = "https://trungtamthuoc.com" + target_url
                        break
                except:
                    continue
            
            if target_url:
                print(f"Navigating to: {target_url}")
                await page.goto(target_url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                
                results["found"] = True
                results["details"]["url"] = target_url
                results["details"]["title"] = await page.title()
                
                # Use extraction logic from knowledge/trungtamthuoc_extract.py
                results["details"]["sdk"] = await extract_table_field_safe(page, "Số đăng ký")
                results["details"]["hoat_chat"] = await extract_table_field_safe(page, "Hoạt chất")
                results["details"]["cong_ty"] = await extract_table_field_safe(page, "Công ty sản xuất")
                
                # Screenshot
                img_path = os.path.join(output_dir, f"{timestamp}_hightamine_evidence.png")
                await page.screenshot(path=img_path)
                results["screenshot"] = img_path
                
            else:
                print("No specific Hightamine link found in search results.")
                results["error"] = "No link found"

        except Exception as e:
            results["error"] = str(e)
            print(f"Error: {e}")
        finally:
            await browser.close()
            
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved: {output_file}")

if __name__ == "__main__":
    asyncio.run(run())
