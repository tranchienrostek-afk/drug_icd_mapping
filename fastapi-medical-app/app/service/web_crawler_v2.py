import asyncio
import logging
import re
from playwright.async_api import async_playwright

# --- 1. SETUP LOGGER ---
logger = logging.getLogger("DrugScraper")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False
    logger.warning("playwright-stealth not found. Running without stealth.")

# Pattern Strict: Bắt định dạng chuẩn VN-..., VD-..., QLD-...
SDK_STRICT_PATTERN = re.compile(
    r'(VN-\d{4,5}-\d{2}|VD-\d{4,5}-\d{2}|QLD-\d+-\d+|GC-\d+-\d+|VNA-\d+-\d+|VNB-\d+-\d+)', 
    re.IGNORECASE
)

# Pattern Context: Bắt sau từ khóa "SĐK", "Số đăng ký"
# Khôi phục hỗ trợ tiếng Việt Đđ
SDK_CONTEXT_PATTERN = re.compile(
    r'(?:Số\s+đăng\s+ký|SĐK|SDK|Reg\.No)[:.]?\s*([A-Za-z0-9\-\/Đđ]+)', 
    re.IGNORECASE
)

# Pattern Công dụng: Tìm đoạn văn bản sau các từ khóa chỉ định
# MỚI: Thêm giới hạn ký tự {0,1500} để tránh lấy cả trang web nếu không tìm thấy điểm ngắt
USAGE_PATTERN = re.compile(
    r'(?:Công dụng|Chỉ định|Tác dụng|Indication|Điều trị)[:.]?\s*(.{10,1500}?)(?=(?:Chống chỉ định|Liều dùng|Tác dụng phụ|Thận trọng|Lưu ý|Bảo quản|Đóng gói|\n\n\n|$))', 
    re.IGNORECASE | re.DOTALL
)

async def scrape_multisource_fallback(keyword, max_results=3):
    """
    [FALLBACK] Tìm kiếm trên Bing và trích xuất thông tin thuốc từ nhiều nguồn.
    """
    # Query tìm kiếm: ưu tiên kết quả Việt Nam từ các trang uy tín
    # Regex này giữ lại tên thuốc, loại bỏ các phần sau dấu - ( hoặc số liệu
    simple_keyword_match = re.match(r'^([a-zA-Z0-9\s]+)', keyword)
    simple_keyword = simple_keyword_match.group(1).strip() if simple_keyword_match else keyword

    trusted_domains = "site:drugbank.vn OR site:thuocbietduoc.com.vn OR site:vinmec.com"
    search_query = f"{simple_keyword} số đăng ký {trusted_domains}"
    
    logger.info(f"Keyword: '{keyword}' -> Search Query: '{search_query}'")
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        if HAS_STEALTH:
            await stealth_async(page)
        
        try:
            logger.info(f"Đang tìm kiếm Bing: {search_query}")
            await page.goto(f"https://www.bing.com/search?q={search_query}&mkt=vi-VN&setLang=vi", timeout=30000)
            
            try:
                # Chờ selector, nếu fail thì thử selector backup
                await page.wait_for_selector("li.b_algo h2 a", timeout=5000)
            except:
                logger.warning("Không tìm thấy selector chính, thử backup...")
                # Đôi khi Bing hiển thị dạng card hoặc layout khác
                if await page.locator(".b_algo").count() == 0:
                     logger.error("Bị chặn hoặc không có kết quả.")
                     return []

            links = []
            elements = await page.query_selector_all("li.b_algo h2 a")
            
            for el in elements:
                url = await el.get_attribute("href")
                if url and url.startswith("http") and not any(x in url for x in ["google", "microsoft", "search", "tim-kiem", "danh-muc", "lazada", "shopee"]):
                    if url not in links:
                        links.append(url)
                if len(links) >= max_results:
                    break
            
            logger.info(f"Tìm thấy {len(links)} link: {links}")
            
            for link in links:
                detail_page = None
                try:
                    detail_page = await context.new_page()
                    # Block media to speed up
                    await detail_page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,mp4,ttf,otf}", lambda route: route.abort())
                    
                    logger.info(f"Đang cào: {link}")
                    try:
                        await detail_page.goto(link, timeout=15000, wait_until="domcontentloaded")
                    except:
                        logger.warning(f"Timeout khi load {link}, bỏ qua.")
                        await detail_page.close()
                        continue
                    
                    body_text = await detail_page.inner_text("body")
                    page_title = await detail_page.title()
                    
                    # --- FIX LOGIC CHECK TIÊU ĐỀ (NỚI LỎNG) ---
                    # Thay vì check nguyên cụm "Ludox - 200mg", ta chỉ check "Ludox"
                    # Tách keyword gốc thành các token (từ đơn)
                    kw_tokens = [t.lower() for t in re.split(r'[\s\-\(\)mg]+', keyword) if len(t) > 2]
                    
                    # Logic: Nếu ÍT NHẤT MỘT từ khóa quan trọng (vd: Ludox) xuất hiện trong Title/URL -> OK
                    is_match = False
                    for token in kw_tokens:
                        if token in page_title.lower() or token in link.lower():
                            is_match = True
                            break
                    
                    if not is_match and len(kw_tokens) > 0:
                        logger.warning(f"-> Bỏ qua: '{page_title}' không chứa token nào trong {kw_tokens}")
                        await detail_page.close()
                        continue

                    # --- TRÍCH XUẤT (Giữ nguyên) ---
                    sdk_match = SDK_STRICT_PATTERN.search(body_text)
                    if sdk_match:
                        sdk_value = sdk_match.group(1)
                    else:
                        context_match = SDK_CONTEXT_PATTERN.search(body_text)
                        sdk_value = context_match.group(1) if context_match else "Not Found"

                    usage_match = USAGE_PATTERN.search(body_text)
                    if usage_match:
                        raw_usage = usage_match.group(1).strip()
                        usage_value = re.sub(r'\s+', ' ', raw_usage)[:400] + "..."
                    else:
                        usage_value = "Not Found"

                    results.append({
                        "source": link,
                        "sdk": sdk_value,
                        "usage": usage_value
                    })

                except Exception as e:
                    logger.error(f"Lỗi khi xử lý link {link}: {e}")
                finally:
                    if detail_page:
                        await detail_page.close()

        except Exception as e:
            logger.error(f"Lỗi Browser: {e}")
        finally:
            await browser.close()
            
    return results

async def scrape_detail_page(context, url):
    """
    Cào chi tiết 1 trang thuốc (Dùng Robust Selectors)
    """
    page = await context.new_page()
    if HAS_STEALTH: await stealth_async(page)
    
    data = {
        "source": url,
        "sdk": "Not Found",
        "usage": "Not Found",
        "official_name": "",
        "ingredients": ""
    }
    
    try:
        # Block media
        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,mp4,ttf,otf}", lambda route: route.abort())
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        
        # 1. Tên thuốc (H1)
        try:
            h1 = await page.wait_for_selector("h1", timeout=5000)
            data["official_name"] = (await h1.inner_text()).strip()
        except: pass
        
        # 2. SĐK
        try:
            sdk_el = page.locator("xpath=//div[contains(text(), 'Số đăng ký')]/following-sibling::div")
            if await sdk_el.count() > 0:
                data["sdk"] = (await sdk_el.first.inner_text()).strip()
        except: pass
        
        # 3. Hoạt chất
        try:
            ing_el = page.locator(".ingredient-content")
            if await ing_el.count() > 0:
                data["ingredients"] = (await ing_el.first.inner_text()).strip()
        except: pass
        
        # 4. Chỉ định (Usage)
        try:
            # Fallback multiple selectors
            usage_el = page.locator("#chi-dinh")
            if await usage_el.count() == 0:
                 usage_el = page.locator("xpath=//h2[contains(text(), 'Chỉ định')]/following-sibling::div")
            
            if await usage_el.count() > 0:
                 data["usage"] = (await usage_el.first.inner_text()).strip()[:500] + "..."
        except: pass

    except Exception as e:
        logger.error(f"Error scraping detail {url}: {e}")
    finally:
        await page.close()
        
    return data

async def scrape_thuocbietduoc_direct(keyword):
    """
    Search trực tiếp trên thuocbietduoc.com.vn theo yêu cầu User
    """
    logger.info(f"--- Direct Search ThuocBietDuoc: '{keyword}' ---")
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        if HAS_STEALTH: await stealth_async(page)
        
        try:
            # 1. Vào trang chủ
            await page.goto("https://thuocbietduoc.com.vn/", timeout=30000)
            
            # 2. Search
            # Selector ID "search-input" is not unique (Mobile/Desktop/Main).
            # Use filter(visible=True) to get the interactable one.
            search_input = page.locator("#search-input").filter(visible=True).first
            await search_input.fill(keyword)
            await search_input.press("Enter")
            
            logger.info("Đã bấm Enter. Đợi 60s theo yêu cầu...")
            await page.wait_for_timeout(60000) # Wait 60s
            
            # 3. Phân tích kết quả (Logic User)
            urls_to_scrape = []
            
            # Selector 1: Check nếu có kết quả đơn (Hoặc layout dạng section[2]/div/div... )
            # User XPath: /html/body/main/section[2]/div/div[2]/div/div/h3/a
            # Chú ý: XPath tuyệt đối user đưa có thể gãy, nhưng ta cứ thử + fallback
            
            # Tìm danh sách các thẻ a trong khung kết quả
            # Khung kết quả thường là section[2] -> ...
            # Để an toàn, ta tìm thẻ h3 > a trong main
            
            # Thử lấy danh sách H3 > A (Tiêu đề thuốc)
            links = page.locator("section h3 a")
            count = await links.count()
            
            if count == 0:
                logger.warning("Không tìm thấy kết quả nào sau 60s.")
            else:
                top_n = min(count, 2) # Lấy tối đa 2
                for i in range(top_n):
                     url = await links.nth(i).get_attribute("href")
                     if url: urls_to_scrape.append(url)
            
            logger.info(f"Tìm thấy {len(urls_to_scrape)} link chi tiết: {urls_to_scrape}")
            
            # 4. Đa luồng cào chi tiết (Parallel)
            tasks = [scrape_detail_page(context, url) for url in urls_to_scrape]
            extracted_items = await asyncio.gather(*tasks)
            results.extend(extracted_items)

        except Exception as e:
            logger.error(f"Lỗi Direct Search: {e}")
        finally:
            await browser.close()
            
    return results

def consolidate_results_v2(keyword, results, source_name="ThuocBietDuoc Direct"):
    if not results:
        return {
            "official_name": keyword,
            "sdk": "Không tìm thấy",
            "usage": "Không tìm thấy thông tin",
            "source": f"{source_name} (No Result)"
        }
    
    # Ưu tiên kết quả đầu tiên hoặc kết quả có SDK
    best_result = results[0]
    for r in results:
        if r.get("sdk") and r.get("sdk") not in ["Not Found", "Đang cập nhật"]:
            best_result = r
            break

    return {
        "official_name": best_result.get("official_name") or keyword,
        "sdk": best_result.get("sdk") if best_result.get("sdk") != "Not Found" else "Đang cập nhật",
        "usage": best_result.get("usage"),
        "hoat_chat": best_result.get("ingredients", ""),
        "source": source_name,
        "ref_link": best_result.get("source")
    }


# --- WRAPPER CHO TƯƠNG THÍCH VỚI CODE CŨ ---
async def scrape_drug_v2(keyword):
    """
    Hàm wrapper để giữ tương thích với services.py
    Input: Tên thuốc
    Output: Dictionary thông tin đã tổng hợp
    """
    # 1. Gọi Direct Search (ThuocBietDuoc)
    raw_results = await scrape_thuocbietduoc_direct(keyword)
    source_used = "ThuocBietDuoc Direct"
    
    # NO FALLBACK (User Request)
    
    # 2. Tổng hợp kết quả
    final_data = consolidate_results_v2(keyword, raw_results, source_used)
    
    return final_data


# --- MAIN RUNNER ---
if __name__ == "__main__":
    # Test
    kw = "Panadol Extra" 
    print(f"--- TESTING SCRAPER FOR: '{kw}' ---")
    
    try:
        raw_data = asyncio.run(scrape_bing_search(kw))
        final_data = consolidate_results(kw, raw_data)
        
        import json
        print("\n[KẾT QUẢ CUỐI CÙNG]")
        print(json.dumps(final_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Main Error: {e}")