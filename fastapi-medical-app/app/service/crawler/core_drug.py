import time
import asyncio
from .utils import logger, SCREENSHOT_DIR
from .extractors import extract_drug_details

async def scrape_single_site_drug(browser, site_config, keyword):
    """Logic cào thuốc (Optimized: Reused Browser + Resource Blocking + Screenshots)"""
    site_name = site_config['TenTrang']
    url = site_config['URL']
    results = []
    
    start_time = time.time()
    logger.info(f"[{site_name}] STARTER - Clean Keyword: '{keyword}'")
    
    # Create new context explicitly with Desktop Viewport and Permissions
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        permissions=['geolocation', 'notifications'],
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
    )
    
    page = await context.new_page()
    
    try:
        logger.info(f"[{site_name}] Navigating to: {url}")
        await page.goto(url, timeout=45000)
        
        if "longchau" in str(url): await asyncio.sleep(1)

        logger.info(f"[{site_name}] Filling search input...")
        try:
             input_selector = site_config['XPath_Input_Search']
             if input_selector.startswith("//") or input_selector.startswith("/html"):
                 input_selector = f"xpath={input_selector}"
             
             await page.wait_for_selector(input_selector, timeout=8000)
             await page.locator(input_selector).first.fill(keyword)
        except Exception as e:
             logger.warning(f"[{site_name}] Input field not found: {e}")
             timestamp = int(time.time())
             shot_path = f"{SCREENSHOT_DIR}/{site_name}_input_error_{timestamp}.png"
             await page.screenshot(path=shot_path)
             logger.info(f"[{site_name}] Screenshot saved: {shot_path}")
             return []
        
        action = str(site_config['HanhDong_TimKiem']).strip()
        if action.upper() == "ENTER": 
            await page.keyboard.press("Enter")
        else: 
            if not action.upper() == "ENTER":
                 try:
                    action_selector = action
                    if action.startswith("//") or action.startswith("/html"):
                        action_selector = f"xpath={action}"
                    await page.wait_for_selector(action_selector, timeout=3000)
                    await page.locator(action_selector).first.click()
                 except: pass
        
        logger.info(f"[{site_name}] Search triggered.")
        await asyncio.sleep(2) 
        
        # --- FIND ITEMS ---
        try: 
            container_selector = site_config['XPath_Item_Container']
            if container_selector.startswith("//") or container_selector.startswith("/html"):
                container_selector = f"xpath={container_selector}"
            
            await page.wait_for_selector(container_selector, timeout=10000)
            items = page.locator(container_selector)
        except: 
            logger.warning(f"[{site_name}] Primary container not found. Trying Smart Fallback...")
            fallback_items = page.locator("a.drug-card-title").or_(page.locator("xpath=//h3/a")).or_(page.locator("xpath=//h2/a")).or_(page.locator(".product-title a"))
            if await fallback_items.count() > 0:
                 logger.info(f"[{site_name}] Fallback Success: Found {await fallback_items.count()} items via common selectors.")
                 items = fallback_items
            else:
                logger.info(f"[{site_name}] Fallback 2: Searching by Keyword Link text...")
                fallback_items = page.locator(f"xpath=//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]")
                if await fallback_items.count() > 0:
                    items = fallback_items
                else:
                    logger.warning(f"[{site_name}] All fallbacks failed.")
                    timestamp = int(time.time())
                    shot_path = f"{SCREENSHOT_DIR}/{site_name}_no_items_{timestamp}.png"
                    await page.screenshot(path=shot_path)
                    return []

        # Check direct link mode
        is_direct_link_mode = False
        sample = items.first
        if await sample.get_attribute("href"):
             is_direct_link_mode = True

        count = await items.count()
        logger.info(f"[{site_name}] Found {count} items.")
        
        for i in range(min(count, int(site_config['Max_Item']))):
            item = items.nth(i)
            link_url = "N/A"
            
            if is_direct_link_mode:
                 link_url = await item.get_attribute("href")
                 if link_url and not link_url.startswith("http"):
                    base = "https://" + url.split("/")[2]
                    link_url = base + link_url
            else:
                link_xp = site_config['XPath_Link_ChiTiet']
                final_xp = None
                if link_xp != "NO_LINK":
                    if link_xp.startswith("xpath="):
                        raw_xp = link_xp.replace("xpath=", "")
                        if raw_xp.startswith("."):
                            final_xp = link_xp 
                        else:
                            final_xp = f"xpath=.//{raw_xp.lstrip('/')}"
                    else:
                        final_xp = f"xpath=.//{link_xp}" if not link_xp.startswith("/") else f"xpath=.{link_xp}"

                if final_xp and await item.locator(final_xp).count() > 0:
                    link_url = await item.locator(final_xp).first.get_attribute("href")
                    if link_url and not link_url.startswith("http"):
                        base = "https://" + url.split("/")[2]
                        link_url = base + link_url
            
            logger.info(f"[{site_name}] Item {i+1}: Link found: {link_url}")

            full_content = "Không lấy được nội dung."
            extracted_fields = {}

            if link_url != "N/A":
                try:
                    logger.info(f"[{site_name}] Opening detail page: {link_url}")
                    new_page = await context.new_page()
                    # Apply blocking
                    await new_page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,ttf,eot,mp4,mp3}", lambda route: route.abort())
                    
                    await new_page.goto(link_url, timeout=30000)
                    await new_page.wait_for_timeout(2000)
                    
                    full_content, extracted_fields = await extract_drug_details(new_page, site_config, site_name, logger)
                    
                    await new_page.close()
                except Exception as details_err:
                    logger.error(f"[{site_name}] Error detailing: {details_err}")
                    extracted_fields = {} 

            results.append({
                "Source": site_name,
                "Link": link_url,
                "Content": full_content.strip(),
                "_extracted_data": extracted_fields 
            })
    except Exception as e:
        logger.error(f"[{site_name}] GLOBAL ERROR: {e}")
        timestamp = int(time.time())
        shot_path = f"{SCREENSHOT_DIR}/{site_name}_global_error_{timestamp}.png"
        await page.screenshot(path=shot_path)
        logger.info(f"[{site_name}] Screenshot saved: {shot_path}")
    finally:
        await context.close()
        elapsed = time.time() - start_time
        logger.info(f"[{site_name}] FINISHED in {elapsed:.2f}s")
            
    return results
