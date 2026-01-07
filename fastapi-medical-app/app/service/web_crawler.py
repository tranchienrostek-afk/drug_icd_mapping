import pandas as pd
import asyncio
import re
import time
import os
import logging
from playwright.async_api import async_playwright

# --- LOGGING SETUP ---
LOG_DIR = "app/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = logging.getLogger("scraper")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File Handler
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "scraper.log"), encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream Handler (Console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# ==============================================================================
# PHẦN 1: CẤU HÌNH WEB SCRAPER (DRUG)
# ==============================================================================
def get_drug_web_config():
    """
    Trả về DataFrame cấu hình các trang web thuốc
    Updated: 2026-01-07 - Specific XPaths from BUG-001 report
    """
    data = {
        "STT": [0, 1, 2],
        "TenTrang": [
            "DAV (Dịch Vụ Công)", 
            "ThuocBietDuoc", 
            "TrungTamThuoc"
        ],
        "URL": [
            "https://dichvucong.dav.gov.vn/congbothuoc/index",
            "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx",
            "https://trungtamthuoc.com.vn/"
        ],
        "XPath_Input_Search": [
            "xpath=/html/body/div[4]/div/div[1]/div/div/div[2]/div[1]/div/input[2]",
            "xpath=//*[@id=\"search-input\"]",
            "xpath=//*[@id=\"txtKeywords\"]"
        ],
        "HanhDong_TimKiem": [
            "xpath=/html/body/div[4]/div/div[1]/div/div/div[2]/div[2]/button[1]",
            "ENTER",
            "ENTER"
        ],
        "XPath_Item_Container": [
            "xpath=/html/body/div[4]/div/div[2]/div[3]/div[2]/table/tbody/tr", 
            "xpath=/html/body/main/section[2]/div/div[2]/div/div/h3/a", 
            "xpath=//*[@id=\"cscontentdetail\"]/div/div/div/strong/a | //*[@id=\"cscontentdetail\"]/div/div/strong/a"
        ],
        "XPath_Link_ChiTiet": [
            "NO_LINK", 
            ".",
            "."
        ],

        "Field_Selectors": [
             None,
             {
                 "ten_thuoc": "//h1 | /html/body/main/div[2]/div/div[1]/div/div/div[2]/h1",
                 "so_dang_ky": "//*[contains(text(), 'Số đăng ký')]/following-sibling::* | //*[contains(text(), 'SĐK')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div[2]",
                 "hoat_chat": "//div[contains(text(), 'Hoạt chất')]/following-sibling::* | //div[contains(text(), 'Thành phần')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[2]/div/div/div/div/a",
                 "ham_luong": "//div[contains(text(), 'Hàm lượng')]/following-sibling::* | //*[@id=\"thanh-phan-hoat-chat\"]/div[2]/table/tbody/tr/td[2]/span",
                 "dang_bao_che": "//div[contains(text(), 'Dạng bào chế')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div/div[2]/div/div[2]",
                 "danh_muc": "//div[contains(text(), 'Nhóm thuốc')]/following-sibling::* | /html/body/main/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div/div[4]/div/a",
                 "chi_dinh": "//h2[contains(text(), 'Chỉ định')]/following-sibling::* | #chi-dinh | //*[@id=\"cong-dung-thuoc\"]/div[2]"
             },
             {
                 "ten_thuoc": "//h1 | //*[@id=\"cscontentdetail\"]/header/div[2]/div/h1/strong",
                 "so_dang_ky": "//*[contains(text(), 'Số đăng ký')]/parent::*/td[2] | //*[@id=\"cscontentdetail\"]/header/div[2]/div/table/tbody/tr[3]/td[2]",
                 "hoat_chat": "//*[contains(text(), 'Hoạt chất')]/parent::*/td[2] | //*[contains(text(), 'Thành phần')]/parent::*/td[2] | //*[@id=\"cs-hoat-chat\"]/td[2]",
                 "ham_luong": "//*[@id=\"pro-mo-ta-noi-dung\"]/table | //*[@id=\"pro-mo-ta-noi-dung\"]/table",
                 "dang_bao_che": "//*[contains(text(), 'Dạng bào chế')]/parent::*/td[2] | //*[@id=\"cscontentdetail\"]/header/div[2]/div/table/tbody/tr[4]/td[2]",
                 "danh_muc": "//*[@id=\"cscategorymain\"]/td[2] | //*[@id=\"cscategorymain\"]/td[2]",
                 "chi_dinh": "//*[@id=\"pro-mo-ta-noi-dung\"]/p[3] | //div[contains(@class, 'cs-content')]"
             }
        ],
        "UuTien": [99, 1, 3],
        "Max_Item": [1, 2, 2]
    }
    df = pd.DataFrame(data)
    return df.sort_values(by='UuTien')

# ==============================================================================
# PHẦN 2: CẤU HÌNH WEB SCRAPER (ICD)
# ==============================================================================
def get_icd_web_config():
    data = {
        "STT": [1],
        "TenTrang": ["ICD Cục KCB"],
        "URL": ["https://icd.kcb.vn/icd-10/icd10"],
        "XPath_Input_Search": ["//*[@id='search']"],
        "HanhDong_TimKiem": ["ENTER"],
        "XPath_Item_Container": ["//*[@id='recommend-box']//li//a"], 
        "XPath_Link_ChiTiet": ["."],
        "XPath_Nut_Mo_Rong": ["//*[@id='detail']/div/div[4]/div/div[2]/dl[4]/div/div[1]/div/div/h5"],
        "XPath_NoiDung_Lay": ["//*[@id='detail']/div/div[4]/div"],
        "UuTien": [1],
        "Max_Item": [1]
    }
    return pd.DataFrame(data)

# ==============================================================================
# PHẦN 3: ENGINE XỬ LÝ (CORE LOGIC)
# ==============================================================================

# --- SCREENSHOT UTILS ---
SCREENSHOT_DIR = "app/logs/screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

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
    # Grant permissions to specific origin if needed, or globally via context
    # Note: permissions arg in new_context applies to all pages in that context
    
    page = await context.new_page()
    
    # --- RESOURCE BLOCKING ---
    # Temporarily disabled to debug layout issues
    # await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,ttf,eot,mp4,mp3}", lambda route: route.abort())
    
    try:
        logger.info(f"[{site_name}] Navigating to: {url}")
        await page.goto(url, timeout=45000)
        
        if "longchau" in str(url): await asyncio.sleep(1)

        logger.info(f"[{site_name}] Filling search input...")
        try:
             # Smart selector: Check if it's XPath or CSS
             input_selector = site_config['XPath_Input_Search']
             if input_selector.startswith("//") or input_selector.startswith("/html"):
                 input_selector = f"xpath={input_selector}"
             # CSS selectors like #id, .class, input#id work directly
             
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
                    # Smart selector for action button
                    action_selector = action
                    if action.startswith("//") or action.startswith("/html"):
                        action_selector = f"xpath={action}"
                    await page.wait_for_selector(action_selector, timeout=3000)
                    await page.locator(action_selector).first.click()
                 except: pass
        
        logger.info(f"[{site_name}] Search triggered.")
        
        # Wait for page to load results
        await asyncio.sleep(2)  # Give time for dynamic content to load
        
        try: 
            # Smart selector for item container
            container_selector = site_config['XPath_Item_Container']
            if container_selector.startswith("//") or container_selector.startswith("/html"):
                container_selector = f"xpath={container_selector}"
            
            await page.wait_for_selector(container_selector, timeout=10000)
            items = page.locator(container_selector)
        except: 
            logger.warning(f"[{site_name}] Primary container not found. Trying Smart Fallback...")
            # --- SMART FALLBACK ---
            # Strategy 1: Look for common drug links
            # Strategy 1: Look for common drug links (Separated for Playwright)
            fallback_items = page.locator("a.drug-card-title").or_(page.locator("xpath=//h3/a")).or_(page.locator("xpath=//h2/a")).or_(page.locator(".product-title a"))
            if await fallback_items.count() > 0:
                 logger.info(f"[{site_name}] Fallback Success: Found {await fallback_items.count()} items via common selectors.")
                 items = fallback_items
            else:
                # Strategy 2: Look for ANY link containing the keyword
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

        # Determine if 'items' are Containers or Direct Links (Fallback)
        # If we found via Fallback H3/a, 'items' ARE the links.
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
                        # Config already extracted absolute or relative xpath with prefix
                        # We need to make it relative to the ITEM. 
                        # Playwright: item.locator("xpath=./div/...") work? 
                        # Usually .locator("xpath=.//...") is safer.
                        # Clean the prefix
                        raw_xp = link_xp.replace("xpath=", "")
                        if raw_xp.startswith("."):
                            final_xp = link_xp # assume formatted correctly as relative
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
            if link_url != "N/A":
                try:
                    logger.info(f"[{site_name}] Opening detail page: {link_url}")
                    new_page = await context.new_page()
                    # Apply blocking
                    await new_page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,ttf,eot,mp4,mp3}", lambda route: route.abort())
                    
                    await new_page.goto(link_url, timeout=30000)
                    await new_page.wait_for_timeout(2000) # Wait for JS content 
                    
                    # --- NEW: Field Extraction Logic ---
                    field_selectors = site_config.get('Field_Selectors')
                    extracted_fields = {}
                    
                    if field_selectors and isinstance(field_selectors, dict):
                        logger.info(f"[{site_name}] Using Field Selectors...")
                        for field, selector in field_selectors.items():
                            try:
                                if not selector: continue
                                # Check selector type
                                sel_str = selector
                                if "|" in selector:
                                     # Union selector, Playwright handles this if distinct selectors, 
                                     # but if mixing xpath and css, we need to be careful.
                                     # Assuming all parts are predominantly XPath if user provided complex ones.
                                     # Or assume the string IS a valid Playwright selector (separated by | or ,)
                                     # But if we used 'xpath=' prefix in config ONLY at start, we might need to propagate it?
                                     # Actually, let's just treat it as a raw selector if it contains |.
                                     # But if it starts with xpath=, strip it and use xpath= wrapper for the whole thing (if compatible)
                                     # Or better: Split by | and wrap each if needed? 
                                     # Playwright supports "xpath=A | xpath=B" ? No, standar XPath union is just A | B.
                                     
                                     if selector.startswith("xpath="):
                                         sel_str = selector # pass as is, assume valid xpath union
                                     elif "//" in selector:
                                         sel_str = f"xpath={selector}"
                                else:
                                    if selector.startswith("//") or selector.startswith("xpath="):
                                        sel_str = f"xpath={selector}" if not selector.startswith("xpath=") else selector
                                    else:
                                        sel_str = selector # CSS
                                
                                # Wait optional (fast check)
                                if await new_page.locator(sel_str).count() > 0:
                                    val = await new_page.locator(sel_str).first.inner_text()
                                    extracted_fields[field] = val.strip()
                                else:
                                    # Fallback for chi_dinh if backup exists
                                    if field == "chi_dinh" and "chi_dinh_bk" in field_selectors:
                                        bk = field_selectors["chi_dinh_bk"]
                                        if await new_page.locator(f"xpath={bk}").count() > 0:
                                            val = await new_page.locator(f"xpath={bk}").first.inner_text()
                                            extracted_fields["chi_dinh"] = val.strip()
                            except Exception as f_err:
                                logger.warning(f"Field '{field}' extract error: {f_err}")

                        # --- NEW: Post-Process Extracted Fields (specifically chi_dinh for TTT) ---
                        if "chi_dinh" in extracted_fields and extracted_fields["chi_dinh"]:
                             raw_cd = extracted_fields["chi_dinh"]
                             
                             if "trungtamthuoc" in site_name.lower():
                                 # Apply TTT Regex to chi_dinh field
                                 pattern = r'(?:^|[\r\n]+)\s*1\.?\s+(?P<muc1>.*?)(?=[\r\n]+\s*2\.?\s+).*?(?:^|[\r\n]+)\s*2\.?\s+(?P<muc2>.*?)(?=[\r\n]+\s*3\.?\s+)'
                                 match = re.search(pattern, raw_cd, re.DOTALL)
                                 if match:
                                     m1 = match.group('muc1').strip()
                                     m2 = match.group('muc2').strip()
                                     processed_cd = f"1. {m1}\n2. {m2}"
                                     # Truncate if still too long (Rule 2: max 100 words approx 600 chars)
                                     if len(processed_cd) > 800:
                                          processed_cd = processed_cd[:800] + "... (Truncated)"
                                     extracted_fields["chi_dinh"] = processed_cd
                                     logger.info(f"[{site_name}] Extracted 'chi_dinh' refined by Regex ({len(processed_cd)} chars).")
                                 else:
                                     # Regex failed, Fallback Truncate
                                     if len(raw_cd) > 800:
                                          extracted_fields["chi_dinh"] = raw_cd[:800] + "... (Truncated)"
                             else:
                                  # Generic Truncation for other sites
                                  if len(raw_cd) > 800:
                                      extracted_fields["chi_dinh"] = raw_cd[:800] + "... (Truncated)"

                    xp_content = site_config['XPath_NoiDung_Lay']
                    try:
                        await new_page.wait_for_selector(f"xpath={xp_content}", timeout=5000)
                        raw_content = await new_page.locator(f"xpath={xp_content}").first.inner_text()
                        
                        # --- NEW: Process Content based on Site ---
                        if "trungtamthuoc" in site_name.lower():
                            # Apply Specific Regex for TTT
                            # Pattern: Robust (?:^|[\r\n]+)\s*1\.?\s+...
                            logger.info(f"[{site_name}] Applying Robust Regex to TTT content...")
                            pattern = r'(?:^|[\r\n]+)\s*1\.?\s+(?P<muc1>.*?)(?=[\r\n]+\s*2\.?\s+).*?(?:^|[\r\n]+)\s*2\.?\s+(?P<muc2>.*?)(?=[\r\n]+\s*3\.?\s+)'
                            match = re.search(pattern, raw_content, re.DOTALL)
                            if match:
                                m1 = match.group('muc1').strip()
                                m2 = match.group('muc2').strip()
                                full_content = f"1. {m1}\n2. {m2}"
                                logger.info(f"[{site_name}] Regex Success. Len: {len(full_content)}")
                            else:
                                full_content = raw_content # Fallback if regex fails (structure changed)
                        else:
                            # Truncate for others
                            full_content = raw_content
                            if len(full_content) > 1000: # Approx 100-200 words
                                full_content = full_content[:1000] + "... (Truncated)"
                                
                        logger.info(f"[{site_name}] Content extracted ({len(full_content)} chars).")
                    except:
                        if extracted_fields:
                            full_content = "Structured Data Extracted: " + str(extracted_fields)
                        else:
                            full_content = await new_page.locator("body").inner_text()
                            full_content = "⚠️ (Fallback) " + full_content[:800]
                        logger.warning(f"[{site_name}] Main content not found, using Fallback.")
                    
                    await new_page.close()
                except Exception as details_err:
                    logger.error(f"[{site_name}] Error detailing: {details_err}")
                    extracted_fields = {} # Reset on error

            results.append({
                "Source": site_name,
                "Link": link_url,
                "Content": full_content.strip(),
                "_extracted_data": extracted_fields if 'extracted_fields' in locals() else {} 
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

# ==============================================================================
# PUBLIC FUNCTIONS (API SẼ GỌI CÁI NÀY)
# ==============================================================================

def parse_drug_info(raw_text):
    """Extract structured info from raw text using Regex"""
    data = {
        "so_dang_ky": None,
        "hoat_chat": None,
        "cong_ty_san_xuat": None,
        "chi_dinh": None, 
        "tu_dong_nghia": None
    }
    
    # SDK Pattern: VN-1234-56, VD-..., V..., QL...
    # Robust patterns for various formats
    patterns = [
        r'(?:SĐK|Số đăng ký|SĐK|SDK|Reg\.No)[:\.]?\s*([A-Z0-9\-\/]{5,20})', # Min 5 chars
        r'(VN-\d{4,10}-\d{2}|VD-\d{4,10}-\d{2}|QLD-\d+-\d+|GC-\d+-\d+|VNA-\d+-\d+|VNB-\d+-\d+)', # Common Patterns
        r'([A-Z]{1,3}-\d{4,10}-\d{2})' # General Pattern
    ]
    
    for p in patterns:
        match = re.search(p, raw_text, re.IGNORECASE)
        if match:
            data["so_dang_ky"] = match.group(1).strip().strip(':').strip('.')
            break
            
    # Simple direct SDK pattern if no prefix found
    if not data["so_dang_ky"]:
        # Match something like VD-12345-12 or VN-123456-12
        match = re.search(r'([A-Z]{1,3}-\d{4,10}-\d{2})', raw_text)
        if match:
             data["so_dang_ky"] = match.group(1)

    # Hoat Chat
    hc_match = re.search(r"(?:Hoạt chất|Thành phần)[:\.]?\s*(.+?)(?:\n|$)", raw_text, re.IGNORECASE)
    if hc_match:
        data["hoat_chat"] = hc_match.group(1).strip()
        
    # Cong Ty
    ct_match = re.search(r"(?:Công ty|Nhà) sản xuất[:\.]?\s*(.+?)(?:\n|$)", raw_text, re.IGNORECASE)
    if ct_match:
        data["cong_ty_san_xuat"] = ct_match.group(1).strip()
        
    return data

async def scrape_drug_web_advanced(keyword):
    """
    Advanced Parallel Search & Merge
    """
    config_df = get_drug_web_config()
    
    # --- Robust Keyword Cleaning ---
    # Replace common separators with spaces to improve search engine matching
    # Added + and / to the list of characters to replace to avoid search errors
    clean_kw = re.sub(r'[-–():+/]', ' ', keyword)
    clean_kw = re.sub(r'\s+', ' ', clean_kw).strip()
    
    # Try multiple search variants if needed
    variants = [clean_kw]
    
    # Fallback variant: Try only the first word or words before the first number (simplified name)
    # e.g., "Paracetamol 500mg" -> "Paracetamol"
    if " " in clean_kw:
        simplified = re.split(r'\d', clean_kw)[0].strip()
        if simplified and simplified != clean_kw and len(simplified) > 2:
            variants.append(simplified)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for kw_variant in variants:
                logger.info(f"[WebAdvanced] Attempting search with: '{kw_variant}'")
                tasks = []
                for _, site in config_df.head(3).iterrows():
                    tasks.append(scrape_single_site_drug(browser, site, kw_variant))
                
                results_lists = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check if we got ANY candidates from this variant
                has_results = False
                for r_list in results_lists:
                    if isinstance(r_list, list) and len(r_list) > 0:
                        # Even if no SDK yet, we take it if we found items
                        has_results = True
                        break
                
                if has_results:
                    logger.info(f"[WebAdvanced] Found potential results for variant: '{kw_variant}'")
                    break 
                else:
                    logger.warning(f"[WebAdvanced] No items found for variant: '{kw_variant}'. Trying fallback...")
        finally:
            await browser.close()

            
    # 2. Flatten & Parse
    candidates = []
    logger.info(f"[WebAdvanced] Flattening results from {len(results_lists)} site lists...")
    for res in results_lists:
        if isinstance(res, list):
            for item in res:
                content = item.get('Content', '')
                parsed = parse_drug_info(content)
                
                # --- NEW: Prefer Extracted Data over Regex ---
                if '_extracted_data' in item and item['_extracted_data']:
                    # Special handling for field data that might contain the label
                    for f_key, f_val in item['_extracted_data'].items():
                        if f_key == "so_dang_ky" and f_val:
                            # If it's something like "Số đăng ký: VN-1234", extract the part
                            sdk_clean = parse_drug_info(f_val).get('so_dang_ky')
                            if sdk_clean: 
                                parsed['so_dang_ky'] = sdk_clean
                            else:
                                # Fallback if no prefix found in field, maybe it is just the value
                                parsed['so_dang_ky'] = f_val.strip()
                        else:
                             parsed[f_key] = f_val
                
                item.update(parsed)
                if 'ten_thuoc' not in item or not item['ten_thuoc']: 
                     item['ten_thuoc'] = keyword 
                
                # Collect ALL items as candidates initially
                candidates.append(item)
    
    logger.info(f"[WebAdvanced] Total items found: {len(candidates)}")
    
    # 3. Stop Condition & Selection
    # If no candidates at all, return not_found
    if not candidates:
        return {"status": "not_found", "message": "No drugs found on web."}
        
    # Prefer candidates with SDK
    sdk_candidates = [c for c in candidates if c.get('so_dang_ky')]
    logger.info(f"[WebAdvanced] Candidates with SDK: {len(sdk_candidates)}")
    
    if not sdk_candidates:
        # Fallback: Just return the best item found even without SDK
        logger.warning(f"[WebAdvanced] No SDK found. Returning best item without SDK.")
        best_candidate = candidates[0]
        # Ensure it has something for merge logic
        if not best_candidate.get('so_dang_ky'): 
             best_candidate['so_dang_ky'] = "Web Result (No SDK)"
        sdk_groups = {"Web Result (No SDK)": [best_candidate]}
    else:
        # Group by SDK
        sdk_groups = {}
        for c in sdk_candidates:
            sdk = c['so_dang_ky']
            if sdk not in sdk_groups: sdk_groups[sdk] = []
            sdk_groups[sdk].append(c)
        
    # Select best group (Max items, or First found)
    sorted_groups = sorted(sdk_groups.values(), key=len, reverse=True)
    best_group = sorted_groups[0]
    
    # 4. Merge Logic
    # Name: Priority first link
    final_name = best_group[0]['ten_thuoc']
    final_sdk = best_group[0]['so_dang_ky']
    
    # Merge unique sets
    hoat_chat_set = {i['hoat_chat'] for i in best_group if i.get('hoat_chat')}
    cong_ty_set = {i['cong_ty_san_xuat'] for i in best_group if i.get('cong_ty_san_xuat')}
    sources = {i['Link'] for i in best_group if i.get('Link')}
    
    # New Fields strategy: Take from best candidate
    best_candidate = best_group[0]
    dang_bao_che = best_candidate.get('dang_bao_che')
    nhom_thuoc = best_candidate.get('nhom_thuoc')
    ham_luong = best_candidate.get('ham_luong')
    
    note_parts = []
    if nhom_thuoc: note_parts.append(f"Nhóm: {nhom_thuoc}")
    if ham_luong: note_parts.append(f"Hàm lượng: {ham_luong}")
    final_note = " | ".join(note_parts)

    # Use extracted chi_dinh if available, else placeholder
    final_chi_dinh = best_candidate.get('chi_dinh')
    if not final_chi_dinh:
         final_chi_dinh = f"Combined from {len(sources)} sources."

    final_data = {
        "ten_thuoc": final_name,
        "so_dang_ky": final_sdk,
        "hoat_chat": " | ".join(filter(None, hoat_chat_set)),
        "cong_ty_san_xuat": " | ".join(filter(None, cong_ty_set)),
        "chi_dinh": final_chi_dinh,
        "classification": dang_bao_che,
        "note": final_note, 
        "source_urls": list(sources),
        "confidence": 0.8,
        "source": "Web Search (Advanced)"
    }
    
    return final_data

async def search_icd_online(keyword):
    """Hàm main tìm kiếm bệnh"""
    config_df = get_icd_web_config()
    
    tasks = [scrape_single_site_icd(row, keyword) for _, row in config_df.iterrows()]
    results_lists = await asyncio.gather(*tasks)
    
    final_results = []
    for lst in results_lists:
        final_results.extend(lst)
        
    return final_results