import asyncio
import pandas as pd
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright

# ================= CONFIG =================
BASE_URL = "https://thuocbietduoc.com.vn/thuoc/drgsearch.aspx"
START_PAGE = 1829
MAX_PAGES = 3424
MAX_WORKERS = 6

# File chứa kết quả
OUTPUT_FILE = f"ketqua_thuoc_part_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
# File ghi nhật ký hoạt động (Để bạn xem lại khi VS Code bị tắt)
HISTORY_LOG_FILE = "session_history.log"
# File ghi lỗi chi tiết
ERROR_LOG_FILE = "error_log_tong.txt"

# ================= LOGGING SYSTEM =================
def logger(message):
    """Ghi log ra cả màn hình console và file lưu trữ"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # In ra console
    print(formatted_message)
    
    # Ghi vào file history (append mode)
    with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted_message + "\n")

# ================= UTILS =================
def log_error_page(page_num, reason):
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] Trang {page_num}: {reason}\n")
    logger(f"❌ LỖI tại trang {page_num}: {reason}")

def save_batch(data_list):
    df = pd.DataFrame(data_list)
    header = not os.path.exists(OUTPUT_FILE)
    df.to_csv(OUTPUT_FILE, mode="a", header=header, index=False, encoding="utf-8-sig")

async def clean_text(page, selector):
    try:
        loc = page.locator(selector)
        if await loc.count() > 0:
            return (await loc.first.inner_text()).strip()
    except:
        pass
    return ""

# ================= DETAIL WORKER =================
async def scrape_detail(context, sem, link):
    async with sem:
        page = await context.new_page()
        try:
            await page.goto(link, timeout=30000, wait_until="domcontentloaded")
            record = {
                "so_dang_ky": await clean_text(page, "xpath=//div[contains(text(),'Số đăng ký')]/following-sibling::div"),
                "ten_thuoc": await clean_text(page, "h1"),
                "hoat_chat": await clean_text(page, ".ingredient-content"),
                "noi_dung_dieu_tri": await clean_text(page, "#chi-dinh") or await clean_text(page, "xpath=//h2[contains(text(),'Chỉ định')]/following-sibling::div"),
                "dang_bao_che": await clean_text(page, "xpath=//div[contains(text(),'Dạng bào chế')]/following-sibling::div"),
                "danh_muc": await clean_text(page, "xpath=//div[contains(text(),'Nhóm thuốc')]/following-sibling::div"),
                "ham_luong": await clean_text(page, "xpath=//div[contains(text(),'Hàm lượng')]/following-sibling::div"),
                "url_nguon": link
            }
            return record
        except Exception as e:
            return None
        finally:
            await page.close()

# ================= MAIN =================
async def main():
    logger("🚀 START ASYNC SCRAPER")
    logger(f"📄 OUTPUT FILE: {OUTPUT_FILE}")
    logger(f"📝 LOG FILE: {HISTORY_LOG_FILE}")

    sem = asyncio.Semaphore(MAX_WORKERS)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--disable-extensions"]
        )

        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        async def block(route):
            if route.request.resource_type in ["image", "font", "stylesheet"]:
                await route.abort()
            else:
                await route.continue_()

        page = await context.new_page()
        await page.route("**/*", block)
        page.set_default_timeout(60000)

        current_page = START_PAGE

        while current_page <= MAX_PAGES:
            logger(f"🔍 Đang quét Trang {current_page}/{MAX_PAGES}...")
            page_url = f"{BASE_URL}?page={current_page}"

            load_success = False
            for attempt in range(3):
                try:
                    await page.goto(page_url, wait_until="domcontentloaded")
                    if await page.locator("xpath=/html/body/main/section[3]/div/div/div/div[2]/div/div/a").count() > 0:
                        load_success = True
                        break
                    await asyncio.sleep(1)
                except:
                    await asyncio.sleep(2)

            if not load_success:
                log_error_page(current_page, "Không load được danh sách sau 3 lần thử")
                current_page += 1
                continue

            try:
                product_locator = page.locator("xpath=/html/body/main/section[3]/div/div/div/div[2]/div/div/a")
                links = []
                count = await product_locator.count()
                for i in range(count):
                    href = await product_locator.nth(i).get_attribute("href")
                    if href: links.append(href)

                logger(f"   -> Tìm thấy {len(links)} link thuốc. Bắt đầu tải chi tiết...")

                tasks = [scrape_detail(context, sem, link) for link in links]
                results = await asyncio.gather(*tasks)
                batch_data = [r for r in results if r]

                if batch_data:
                    save_batch(batch_data)
                    logger(f"   ✅ Đã lưu {len(batch_data)}/{len(links)} thuốc vào CSV.")
                else:
                    log_error_page(current_page, "Không lấy được dữ liệu chi tiết (Trang trắng)")

            except Exception as e:
                log_error_page(current_page, f"Lỗi thực thi: {str(e)}")

            current_page += 1

        await browser.close()
        logger("✅ CHƯƠNG TRÌNH HOÀN THÀNH")

if __name__ == "__main__":
    asyncio.run(main())