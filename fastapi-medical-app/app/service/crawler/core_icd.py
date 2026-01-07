import asyncio
from playwright.async_api import async_playwright
from .config import get_icd_web_config

async def scrape_single_site_icd(site_config, keyword):
    """Logic cào bệnh (Giữ nguyên logic click mở rộng)"""
    site_name = site_config['TenTrang']
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"   -> [Web] Truy cập: {site_name}")
            await page.goto(site_config['URL'], timeout=60000)
            await page.locator(site_config['XPath_Input_Search']).fill(keyword)
            await page.keyboard.press("Enter")
            
            try:
                await page.wait_for_selector("//*[@id='recommend-box']//li", timeout=10000)
            except:
                return []

            items = page.locator(site_config['XPath_Item_Container'])
            count = await items.count()

            if count > 0:
                target_index = -1
                for i in range(count):
                    text = await items.nth(i).inner_text()
                    if keyword.upper() in text.upper():
                        target_index = i
                        break
                
                if target_index == -1: target_index = count - 1 # Fallback node cuối

                target_item = items.nth(target_index)
                await target_item.scroll_into_view_if_needed()
                await target_item.click()
                await asyncio.sleep(2)

                # --- LOGIC CLICK MỞ RỘNG (EXPAND) ---
                xp_expand = site_config['XPath_Nut_Mo_Rong']
                try:
                    expand_btn = page.locator(xp_expand)
                    if await expand_btn.count() > 0 and await expand_btn.is_visible():
                        await expand_btn.click()
                        await asyncio.sleep(1)
                    else:
                        # Fallback click all h5
                        tabs = page.locator("//*[@id='detail']//h5")
                        cnt_tabs = await tabs.count()
                        for t in range(cnt_tabs):
                            await tabs.nth(t).click()
                            await asyncio.sleep(0.5)
                except: pass

                xp_content = site_config['XPath_NoiDung_Lay']
                content = "Không lấy được nội dung"
                try:
                    await page.wait_for_selector(xp_content, timeout=5000)
                    content = await page.locator(xp_content).inner_text()
                except:
                    content = await page.locator("#detail").inner_text()

                results.append({
                    "Source": site_name,
                    "Link": "https://icd.kcb.vn",
                    "Content": content.strip()
                })
        except: pass
        finally:
            await browser.close()
    return results

async def search_icd_online(keyword):
    """Hàm main tìm kiếm bệnh"""
    config_df = get_icd_web_config()
    
    tasks = [scrape_single_site_icd(row, keyword) for _, row in config_df.iterrows()]
    results_lists = await asyncio.gather(*tasks)
    
    final_results = []
    for lst in results_lists:
        final_results.extend(lst)
        
    return final_results
