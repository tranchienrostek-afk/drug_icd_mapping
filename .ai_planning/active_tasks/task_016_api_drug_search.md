Sếp gợi ý code
Tiến hành tham khảo xem có được không
Đọc hiểu và kế thừa những cái hay của nhau
Thay vì sửa trực tiếp code, tiến hành tạo các bản copy hoặc backup trước khi tiến hành sửa đổi

extractors.py
import re
from .utils import parse_drug_info

async def extract_drug_details(target, site_config, site_name, logger):
    """
    Trích xuất dữ liệu chi tiết thuốc sử dụng Playwright Page/Locator.
    
    Cập nhật v2 (Fix BUG-011): 
    - Tích hợp logic 'Sibling Finding' từ Bulk Scraper thành công.
    - Tìm Label (text) -> Lấy thẻ div kế bên (thay vì cố đoán selector bảng/tr/td).
    """
    fields_config = site_config.get('fields', {})
    extracted_fields = {}
    full_content = ""

    # --- 1. LẤY FULL CONTENT (Dùng cho RAG/Search) ---
    try:
        # Ưu tiên lấy trong vùng nội dung chính để loại bỏ header/footer
        main_content = target.locator("main, #content, .content, article, body")
        if await main_content.count() > 0:
            full_content = await main_content.first.inner_text()
        else:
            full_content = await target.inner_text("body")
    except Exception as e:
        full_content = ""
        # logger.warning(f"Could not extract full content: {e}")

    # --- 2. CHIẾN THUẬT: THUOCBIETDUOC SPECIFIC (Logic chiến thắng) ---
    # Logic này copy từ script chạy tay: Tìm text label -> lấy div anh em ngay sau nó
    if "thuocbietduoc" in site_name.lower():
        logger.info(f"[{site_name}] Applying 'Sibling Finding' strategy...")
        
        # Mapping: Tên trường -> Các Label có thể xuất hiện trên UI
        sibling_map = {
            "so_dang_ky": ["Số đăng ký", "SĐK", "Reg.No"],
            "dang_bao_che": ["Dạng bào chế", "Bào chế"],
            "quy_cach_dong_goi": ["Quy cách đóng gói", "Đóng gói"],
            "cong_ty_sx": ["Công ty sản xuất", "Nhà sản xuất"],
            "nuoc_sx": ["Nước sản xuất"],
            "cong_ty_dk": ["Công ty đăng ký", "Đơn vị đăng ký"],
            "nhom_thuoc": ["Nhóm thuốc"],
            "ham_luong": ["Hàm lượng", "Nồng độ"]
        }

        # A. Xử lý các trường đặc biệt (Class/Tag cụ thể)
        try:
            # Tên thuốc (thường là H1)
            if await target.locator("h1").count() > 0:
                extracted_fields["ten_thuoc"] = (await target.locator("h1").first.inner_text()).strip()
            
            # Hoạt chất (Class .ingredient-content rất chuẩn trên site này)
            if await target.locator(".ingredient-content").count() > 0:
                extracted_fields["hoat_chat"] = (await target.locator(".ingredient-content").first.inner_text()).strip()
            elif await target.locator("#chi-dinh").count() > 0: # Fallback đôi khi nó nằm lung tung
                 pass
        except Exception:
            pass

        # B. Xử lý các trường Sibling (Label -> Value)
        for field, labels in sibling_map.items():
            if field in extracted_fields: continue # Đã có rồi thì thôi

            for label in labels:
                # XPath thần thánh: Tìm div chứa text label, lấy div ngay sau nó
                # Cấu trúc: <div>Label:</div> <div>Value</div>
                xpath = f"//div[contains(text(), '{label}')]/following-sibling::div"
                try:
                    loc = target.locator(f"xpath={xpath}")
                    if await loc.count() > 0:
                        val = (await loc.first.inner_text()).strip()
                        # Clean bớt rác nếu có (VD: ": ")
                        val = val.lstrip(":").strip()
                        if val:
                            extracted_fields[field] = val
                            logger.info(f"   + Found {field} via label '{label}': {val[:30]}...")
                            break # Found match for this field
                except Exception:
                    continue

    # --- 3. CHIẾN THUẬT: CONFIG-BASED (Fallback cho site khác hoặc trường thiếu) ---
    if fields_config:
        # logger.info(f"[{site_name}] Checking config selectors for missing fields...")
        for field, selectors in fields_config.items():
            if field in extracted_fields and extracted_fields[field]: 
                continue # Skip nếu logic trên đã tìm thấy
            
            for sel in selectors:
                try:
                    if not sel: continue
                    
                    # Chuẩn hóa selector
                    final_sel = sel
                    if not final_sel.startswith("xpath=") and (final_sel.startswith("//") or final_sel.startswith("./")):
                        final_sel = f"xpath={final_sel}"
                    
                    if await target.locator(final_sel).count() > 0:
                        val = await target.locator(final_sel).first.inner_text()
                        if val:
                            extracted_fields[field] = val.strip()
                            break
                except Exception:
                    continue
    
    return full_content, extracted_fields


core_drug.py
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
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ignore_https_errors=True
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