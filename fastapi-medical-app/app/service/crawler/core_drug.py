import time
import asyncio
from .utils import logger, SCREENSHOT_DIR
from .extractors import extract_drug_details

async def try_selectors(page, selectors, timeout=5000):
    """
    Try multiple selectors, return the first one that works.
    Supports both CSS and XPath (prefix with 'xpath=' or '//' detection).
    """
    for sel in selectors:
        try:
            if sel.startswith("//") or sel.startswith("/html"):
                final_sel = f"xpath={sel}"
            else:
                final_sel = sel
            
            locator = page.locator(final_sel)
            if await locator.count() > 0:
                return final_sel, locator.first
        except:
            continue
    
    # None found, try with wait as last resort
    for sel in selectors:
        try:
            if sel.startswith("//") or sel.startswith("/html"):
                final_sel = f"xpath={sel}"
            else:
                final_sel = sel
            
            await page.wait_for_selector(final_sel, timeout=timeout)
            return final_sel, page.locator(final_sel).first
        except:
            continue
    
    return None, None

async def scrape_single_site_drug(browser, site_config, keyword):
    """
    Logic cào thuốc (v4 - BUG-010 Lesson Learn Applied)
    - Resource blocking (faster loading)
    - Higher timeout (60s)
    - Retry logic (3 attempts)
    - Stable browser args
    """
    site_name = site_config['site_name']
    url = site_config['url']
    results = []
    
    start_time = time.time()
    logger.info(f"[{site_name}] STARTER - Clean Keyword: '{keyword}'")
    
    # LESSON 1: Better context with ignore_https_errors
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        ignore_https_errors=True,
        extra_http_headers={
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Upgrade-Insecure-Requests": "1"
        }
    )
    
    page = await context.new_page()
    
    # LESSON 2: Block resources for faster loading
    async def block_resources(route):
        if route.request.resource_type in ["image", "font", "stylesheet"]:
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*", block_resources)
    
    # LESSON 3: Higher timeout (60s instead of 30s)
    page.set_default_timeout(60000)
    
    try:
        logger.info(f"[{site_name}] Navigating to: {url}")
        
        # LESSON 4: Retry logic for navigation
        nav_success = False
        for attempt in range(3):
            try:
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                nav_success = True
                break
            except Exception as nav_err:
                logger.warning(f"[{site_name}] Nav attempt {attempt+1}/3 failed: {nav_err}")
                await asyncio.sleep(2)
        
        if not nav_success:
            logger.error(f"[{site_name}] NETWORK ERROR: All navigation attempts failed")
            return []
        
        # --- SEARCH PHASE with Retry ---
        search_cfg = site_config['search']
        input_selectors = search_cfg.get('input_selectors', [])
        
        search_success = False
        for attempt in range(3):
            try:
                logger.info(f"[{site_name}] Finding search input (attempt {attempt+1})...")
                found_sel, input_el = await try_selectors(page, input_selectors, timeout=10000)
                
                if not input_el:
                    logger.warning(f"[{site_name}] Input not found, retrying...")
                    await asyncio.sleep(2)
                    continue
                
                logger.info(f"[{site_name}] Found input using: {found_sel}")
                await input_el.fill(keyword)
                
                # Execute Action
                action_type = search_cfg['action_type']
                if action_type == "ENTER":
                    await page.keyboard.press("Enter")
                elif action_type == "CLICK":
                    btn_selectors = search_cfg.get('button_selectors', [])
                    if btn_selectors:
                        _, btn_el = await try_selectors(page, btn_selectors, timeout=5000)
                        if btn_el:
                            await btn_el.click()
                        else:
                            await page.keyboard.press("Enter")
                
                search_success = True
                break
            except Exception as e:
                logger.warning(f"[{site_name}] Search attempt {attempt+1}/3 failed: {e}")
                await asyncio.sleep(2)
        
        if not search_success:
            logger.error(f"[{site_name}] SEARCH ERROR: All attempts failed")
            return []
        
        logger.info(f"[{site_name}] Search triggered. Waiting for results...")
        
        # LESSON 5: Wait longer for dynamic content
        await asyncio.sleep(3)
        
        # --- LIST PHASE ---
        list_cfg = site_config['list_logic']
        container_sel = list_cfg['item_container']
        
        if container_sel.startswith("//"):
            container_sel = f"xpath={container_sel}"
        
        try:
            await page.wait_for_selector(container_sel, timeout=15000)
            items = page.locator(container_sel)
        except:
            logger.warning(f"[{site_name}] No items found with selector: {container_sel}")
            items = page.locator("xpath=//non-existent")
        
        count = await items.count()
        logger.info(f"[{site_name}] Found {count} items.")
        
        if count == 0:
            return []
        
        # --- DETAIL PHASE ---
        detail_cfg = site_config['detail_logic']
        has_detail = detail_cfg['has_detail_page']
        max_items = list_cfg.get('max_items', 2)

        for i in range(min(count, max_items)):
            item = items.nth(i)
            link_url = "N/A"
            
            if has_detail:
                link_xp = detail_cfg['link_xpath']
                target_el = item if link_xp == "." else item.locator(link_xp)
                
                if await target_el.count() > 0:
                    link_url = await target_el.first.get_attribute("href")
                    if link_url and not link_url.startswith("http"):
                        base = "https://" + url.split("/")[2]
                        link_url = base + link_url
            else:
                link_url = "In-Page"

            logger.info(f"[{site_name}] Item {i+1}: Link: {link_url}")

            full_content = ""
            extracted_fields = {}

            if has_detail and link_url.startswith("http"):
                try:
                    new_page = await context.new_page()
                    await new_page.route("**/*", block_resources)
                    await new_page.goto(link_url, timeout=60000, wait_until="domcontentloaded")
                    full_content, extracted_fields = await extract_drug_details(new_page, site_config, site_name, logger)
                    await new_page.close()
                except Exception as err:
                    logger.error(f"[{site_name}] Detail error: {err}")
            elif not has_detail:
                try:
                    fields_cfg = site_config.get('fields', {})
                    for field, sels in fields_cfg.items():
                        for sel in sels:
                            try:
                                cell = item.locator(sel)
                                if await cell.count() > 0:
                                    extracted_fields[field] = await cell.first.inner_text()
                                    break
                            except:
                                continue
                except Exception as e:
                    logger.warning(f"[{site_name}] In-page extraction error: {e}")

            results.append({
                "Source": site_name,
                "Link": link_url,
                "Content": full_content.strip() if full_content else "",
                "_extracted_data": extracted_fields
            })
            
    except Exception as e:
        logger.error(f"[{site_name}] GLOBAL ERROR: {e}")
    finally:
        await context.close()
        elapsed = time.time() - start_time
        logger.info(f"[{site_name}] FINISHED in {elapsed:.2f}s")
            
    return results
