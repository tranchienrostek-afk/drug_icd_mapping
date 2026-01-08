from playwright.sync_api import sync_playwright
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThuocBietDuocCrawler")

BASE_URL = "https://thuocbietduoc.com.vn"
MAX_WAIT_PAGE = 90_000   # 90s – web siêu chậm
MAX_WAIT_ELEMENT = 15_000

# Get Headless mode from environment variable (default to True for Docker)
HEADLESS_ENV = os.getenv("HEADLESS", "true").lower() == "true"


# --------------------------------------------------
# SAFE WAIT (KHÔNG TIN LOAD STATE)
# --------------------------------------------------
def safe_wait(seconds=2):
    time.sleep(seconds)


# --------------------------------------------------
# FIND SEARCH INPUT – BẤT KHẢ CHIẾN BẠI
# --------------------------------------------------
def find_search_input(page):
    selectors = [
        "#search-input",
        "input[name='key']",
        "//input[contains(@placeholder,'Tìm')]",
        "//input[contains(@aria-label,'Tìm')]",
        "//input[@type='text']"
    ]

    for s in selectors:
        try:
            el = page.locator(s).first
            el.wait_for(timeout=MAX_WAIT_ELEMENT)
            if el.is_visible():
                return el
        except:
            continue

    # BRUTE FORCE – QUÉT TOÀN BỘ INPUT
    inputs = page.locator("input")
    for i in range(inputs.count()):
        try:
            el = inputs.nth(i)
            ph = (el.get_attribute("placeholder") or "").lower()
            name = (el.get_attribute("name") or "").lower()
            aria = (el.get_attribute("aria-label") or "").lower()

            if "tìm" in ph or "search" in name or "tìm" in aria:
                return el
        except:
            continue

    return None


# --------------------------------------------------
# SUBMIT SEARCH – ENTER → BUTTON
# --------------------------------------------------
def submit_search(page, keyword):
    search_input = find_search_input(page)
    if not search_input:
        logger.warning("❌ Không tìm được ô search")
        return False

    try:
        search_input.fill(keyword)
        safe_wait(1)
    except:
        return False

    # ENTER
    try:
        search_input.press("Enter")
        safe_wait(5)
        return True
    except:
        pass

    # BUTTON SEARCH (ICON)
    try:
        btn = page.locator("//button//i[contains(@class,'fa-search')]").first
        btn.click()
        safe_wait(5)
        return True
    except:
        pass

    return False


# --------------------------------------------------
# EXTRACT PRODUCT LINKS – MAX 2
# --------------------------------------------------
def extract_product_links(page, max_links=2):
    results = []
    seen = set()

    try:
        cards = page.locator("a[href*='/thuoc-']")
        count = cards.count()

        for i in range(count):
            if len(results) >= max_links:
                break

            try:
                a = cards.nth(i)
                href = a.get_attribute("href")
                text = a.inner_text().strip()

                if not href:
                    continue

                if not href.startswith("http"):
                    continue

                if href in seen:
                    continue

                seen.add(href)

                results.append({
                    "name": text,
                    "url": href
                })
            except:
                continue

    except Exception as e:
        logger.error(f"Lỗi lấy link: {e}")

    return results


# --------------------------------------------------
# MAIN FUNCTION – CHỈ TÌM LINK
# --------------------------------------------------
def find_drug_links_thuocbietduoc(drug_name, headless=HEADLESS_ENV):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        page = browser.new_page()

        try:
            logger.info(f"Opening {BASE_URL}...")
            page.goto(BASE_URL, timeout=MAX_WAIT_PAGE)
            page.screenshot(path="01_home_page.png")
            safe_wait(5)

            logger.info(f"Searching for '{drug_name}'...")
            ok = submit_search(page, drug_name)
            page.screenshot(path="02_after_search.png")
            
            if not ok:
                logger.error("Search submission failed")
                return []

            safe_wait(8)
            page.screenshot(path="03_search_results.png")

            links = extract_product_links(page, max_links=2)
            logger.info(f"Found {len(links)} links")
            return links

        finally:
            browser.close()


# --------------------------------------------------
# TEST
# --------------------------------------------------
if __name__ == "__main__":
    print("Starting search for Topsea - F...")
    links = find_drug_links_thuocbietduoc("Topsea - F", headless=True)
    print(f"Search finished. Found {len(links)} links.")
    for l in links:
        print(l)
