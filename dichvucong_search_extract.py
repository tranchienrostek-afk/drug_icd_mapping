import os
import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError

# ================== LOGGER ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DAV_SCRAPER")

# ================== CONFIG ==================
URL = "https://dichvucong.dav.gov.vn/congbothuoc/index"
SEARCH_TIMEOUT = 60000
TABLE_TIMEOUT = 90000

HEADLESS_ENV = os.getenv("HEADLESS", "true").lower() == "true"

# ================== SAFE UTILS ==================
async def safe_text(td):
    try:
        return (await td.inner_text()).strip()
    except:
        return ""

# ================== MAIN SCRAPER ==================
async def scrape_dav(keyword: str):
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS_ENV,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = await browser.new_context()
        page = await context.new_page()

        logger.info("🌐 Mở trang DAV...")
        await page.goto(URL, timeout=SEARCH_TIMEOUT)

        # ---------- SEARCH INPUT ----------
        try:
            search_input = page.locator("input[ng-model='vm.filterAll']")
            await search_input.wait_for(timeout=SEARCH_TIMEOUT)
            await search_input.fill(keyword)
            await search_input.press("Enter")
            logger.info(f"🔎 Đã tìm kiếm: {keyword}")
            await page.screenshot(path="dichvucong_after_search.png")
        except TimeoutError:
            logger.error("❌ Không tìm thấy ô search")
            await browser.close()
            return results

        # ---------- WAIT TABLE ----------
        try:
            await page.wait_for_selector(
                "div.k-grid-content tbody tr",
                timeout=TABLE_TIMEOUT
            )
            logger.info("📊 Bảng dữ liệu đã load")
        except TimeoutError:
            logger.warning("⚠️ Không có dữ liệu")
            await browser.close()
            return results

        # ---------- PARSE ROWS ----------
        rows = page.locator("div.k-grid-content tbody tr")
        count = await rows.count()
        logger.info(f"📄 Số dòng: {count}")

        for i in range(count):
            row = rows.nth(i)
            tds = row.locator("td")
            td_count = await tds.count()

            def get(idx):
                return tds.nth(idx) if idx < td_count else None

            record = {
                "stt": await safe_text(get(1)),
                "so_gplh": await safe_text(get(3)),
                "ngay_het_han_sdk": await safe_text(get(4)),
                "ten_thuoc": await safe_text(get(5)),
                "hoat_chat": await safe_text(get(9)),
                "ham_luong": await safe_text(get(10)),
                "so_quyet_dinh": await safe_text(get(11)),
                "nam_cap": await safe_text(get(12)),
                "dot_cap": await safe_text(get(13)),
                "dang_bao_che": await safe_text(get(14)),
                "dong_goi": await safe_text(get(15)),
                "tieu_chuan": await safe_text(get(16)),
                "tuoi_tho": await safe_text(get(17)),
                "cty_dang_ky": await safe_text(get(18)),
                "nuoc_dk": await safe_text(get(19)),
                "dia_chi_dk": await safe_text(get(20)),
                "cty_san_xuat": await safe_text(get(21)),
                "nuoc_sx": await safe_text(get(22)),
                "dia_chi_sx": await safe_text(get(23)),
            }

            results.append(record)

        await browser.close()
        logger.info("✅ Hoàn tất scrape")
        return results

# ================== RUN ==================
if __name__ == "__main__":
    data = asyncio.run(scrape_dav("Empatince"))
    for d in data:
        print(d)
