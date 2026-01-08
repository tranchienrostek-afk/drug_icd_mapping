from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SearchLinkFinder")

BASE_URL = "https://trungtamthuoc.com"


# --------------------------------------------------
# FIND SEARCH INPUT (BẤT TỬ)
# --------------------------------------------------
def find_search_input(page):
    strategies = [
        "#txtKeywords",
        "input[name='txtKeywords']",
        "//input[contains(@placeholder,'tìm')]",
        "//input[contains(@class,'search')]",
        "//input[@type='text']"
    ]

    for s in strategies:
        try:
            locator = page.locator(s).first
            locator.wait_for(timeout=2000)
            if locator.is_visible():
                return locator
        except:
            continue

    # brute-force fallback
    inputs = page.locator("input")
    for i in range(inputs.count()):
        try:
            el = inputs.nth(i)
            ph = (el.get_attribute("placeholder") or "").lower()
            name = (el.get_attribute("name") or "").lower()
            if "tìm" in ph or "search" in name:
                return el
        except:
            continue

    return None


# --------------------------------------------------
# SUBMIT SEARCH (ENTER → BUTTON)
# --------------------------------------------------
def submit_search(page, keyword: str) -> bool:
    search_input = find_search_input(page)
    if not search_input:
        logger.warning("Không tìm thấy ô search")
        return False

    try:
        search_input.fill(keyword)
    except:
        return False

    # ENTER
    try:
        search_input.press("Enter")
        page.wait_for_load_state("networkidle", timeout=5000)
        return True
    except:
        pass

    # BUTTON
    try:
        btn = page.locator("#btnsearchheader").first
        btn.click()
        page.wait_for_load_state("networkidle", timeout=5000)
        return True
    except:
        pass

    return False


# --------------------------------------------------
# EXTRACT PRODUCT LINKS (MAX 2)
# --------------------------------------------------
def extract_product_links(page, max_links=2):
    results = []

    try:
        products = page.locator(".cs-item-product")
        count = products.count()

        for i in range(min(count, max_links)):
            try:
                a = products.nth(i).locator("a[href]").first
                href = a.get_attribute("href")
                name = a.inner_text().strip()

                if href:
                    full_url = BASE_URL + href if href.startswith("/") else href
                    results.append({
                        "name": name,
                        "url": full_url
                    })
            except:
                continue

    except Exception as e:
        logger.error(f"Lỗi lấy link: {e}")

    return results


# --------------------------------------------------
# MAIN FUNCTION – CHỈ TRẢ LINK
# --------------------------------------------------
def find_drug_links(drug_name: str, headless=True) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            page.goto(BASE_URL, timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            ok = submit_search(page, drug_name)
            if not ok:
                return []

            links = extract_product_links(page, max_links=2)
            return links

        finally:
            browser.close()


# --------------------------------------------------
# TEST
# --------------------------------------------------
if __name__ == "__main__":
    links = find_drug_links("paracetamol 500mg", headless=True)
    for l in links:
        print(l)
