import time
import asyncio
from .utils import logger, SCREENSHOT_DIR
from .extractors import extract_drug_details
from .stealth_config import (
    STEALTH_INIT_SCRIPT, 
    get_random_user_agent,
    human_pause,
    simulate_human_behavior
)

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

async def register_auto_popups(page, selectors=None):
    """
    Register auto-closing handlers for popups.
    """
    potential_selectors = [
        "button[aria-label='Close']",
        ".close-button",
        ".modal-close",
        "span:text('X')",
        "button:text('Đóng')",
        "div[class*='popup'] .close",
        "#close-popup"
    ]
    if selectors:
        potential_selectors = selectors + potential_selectors
    
    # Function disabled/reverted
    pass

async def handle_popups(page, selectors=None):
    """
    Look for and close common popups or overlays.
    """
    potential_selectors = [
        "button[aria-label='Close']",
        ".close-button",
        ".modal-close",
        "span:text('X')",
        "button:text('Đóng')",
        "div[class*='popup'] .close",
        "#close-popup"
    ]
    if selectors:
        potential_selectors = selectors + potential_selectors
        
    for sel in potential_selectors:
        try:
            # Check if exists and visible
            locator = page.locator(sel).first
            if await locator.is_visible():
                logger.info(f"Closing popup found with: {sel}")
                await locator.click()
                await asyncio.sleep(0.5)
        except:
            continue

async def scrape_single_site_drug(browser, site_config, keyword, direct_url=None):
    """
    Logic cào thuốc (v6 - Popup Handling & Improved Stability)
    """
    site_name = site_config.get('site_name', 'Unknown')
    url = site_config.get('url')
    results = []
    
    start_time = time.time()
    logger.info(f"[{site_name}] STARTER - Clean Keyword: '{keyword}'")
    
    popup_selectors = site_config.get('popup_selectors', [])
    
    context = await browser.new_context(
        user_agent=get_random_user_agent(),  # Stealth: Random UA
        ignore_https_errors=True,
        viewport={'width': 1920, 'height': 1080},  # Larger viewport
        locale="vi-VN",
        timezone_id="Asia/Ho_Chi_Minh",
    )
    
    # Stealth: Inject anti-detection script
    await context.add_init_script(STEALTH_INIT_SCRIPT)
    
    page = await context.new_page()
    
    # Block heavy resources
    # Block heavy resources
    async def block_resources(route):
        if route.request.resource_type in ["image", "font", "media", "other"]:
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*", block_resources)
    
    page.set_default_timeout(60000)
    
    try:
        # --- DIRECT URL PATH ---
        if direct_url:
            logger.info(f"[{site_name}] Navigating directly to: {direct_url}")
            await page.goto(direct_url, timeout=60000, wait_until="domcontentloaded")
            await page.goto(direct_url, timeout=60000, wait_until="domcontentloaded")
            # await register_auto_popups(page, popup_selectors)
            await handle_popups(page, popup_selectors)
            
            full_content, extracted_fields = await extract_drug_details(page, site_config, site_name, logger)
            results.append({
                "Source": site_name,
                "Link": direct_url,
                "Content": full_content.strip() if full_content else "",
                "_extracted_data": extracted_fields
            })
            
        # --- ORIGINAL SEARCH PATH ---
        else:
            logger.info(f"[{site_name}] Navigating to search: {url}")
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            # await register_auto_popups(page, popup_selectors)
            await handle_popups(page, popup_selectors)
            
            search_cfg = site_config.get('search', {})
            input_selectors = search_cfg.get('input_selectors', [])
            
            found_sel, input_el = await try_selectors(page, input_selectors, timeout=10000)
            if not input_el:
                logger.error(f"[{site_name}] SEARCH ERROR: Input not found")
                return []
            
            await input_el.fill(keyword)
            
            action_type = search_cfg.get('action_type', 'ENTER')
            if action_type == "ENTER":
                await page.keyboard.press("Enter")
            else:
                btn_sels = search_cfg.get('button_selectors', [])
                _, btn_el = await try_selectors(page, btn_sels, timeout=5000)
                if btn_el:
                    await btn_el.click()
                else:
                    await page.keyboard.press("Enter")
            
            # Stabilization wait after search
            logger.info(f"[{site_name}] Waiting for results to load...")
            await asyncio.sleep(4) 
            await asyncio.sleep(4) 
            await handle_popups(page, popup_selectors)
            
            # --- LIST PHASE ---
            list_cfg = site_config.get('list_logic', {})
            container_sel = list_cfg.get('item_container', 'a')
            
            try:
                # Use wait_for_selector for robustness
                effective_sel = f"xpath={container_sel}" if container_sel.startswith("//") else container_sel
                await page.wait_for_selector(effective_sel, timeout=15000)
                items = page.locator(effective_sel)
            except:
                logger.warning(f"[{site_name}] No list items found with {container_sel}")
                return []
            
            count = await items.count()
            logger.info(f"[{site_name}] Found {count} items.")
            
            detail_cfg = site_config.get('detail_logic', {})
            max_items = list_cfg.get('max_items', 1)
            
            for i in range(min(count, max_items)):
                item = items.nth(i)
                link_url = ""
                
                if detail_cfg.get('has_detail_page'):
                    link_xp = detail_cfg.get('link_xpath', '.')
                    target_el = item if link_xp == "." else item.locator(link_xp)
                    
                    if await target_el.count() > 0:
                        raw_href = await target_el.first.get_attribute("href")
                        if raw_href:
                            from urllib.parse import urljoin
                            link_url = urljoin(url, raw_href)
                            
                if link_url:
                    logger.info(f"[{site_name}] Item {i+1}: Navigating to detail {link_url}")
                    try:
                        detail_page = await context.new_page()
                        await detail_page.route("**/*", block_resources)
                        await detail_page.goto(link_url, timeout=60000, wait_until="domcontentloaded")
                        await detail_page.goto(link_url, timeout=60000, wait_until="domcontentloaded")
                        # await register_auto_popups(detail_page, popup_selectors)
                        await handle_popups(detail_page, popup_selectors)
                        
                        content, fields = await extract_drug_details(detail_page, site_config, site_name, logger)
                        results.append({
                            "Source": site_name,
                            "Link": link_url,
                            "Content": content.strip() if content else "",
                            "_extracted_data": fields
                        })
                        await detail_page.close()
                    except Exception as d_err:
                        logger.error(f"[{site_name}] Detail extraction failed: {d_err}")
                else:
                    # In-page extraction
                    logger.info(f"[{site_name}] Item {i+1}: Extracting in-page (No detail link)")
                    # Logic for non-detail sites could go here if needed
                    pass
            
    except Exception as e:
        logger.error(f"[{site_name}] GLOBAL ERROR: {e}")
    finally:
        await context.close()
        elapsed = time.time() - start_time
        logger.info(f"[{site_name}] FINISHED in {elapsed:.2f}s")
            
    return results
