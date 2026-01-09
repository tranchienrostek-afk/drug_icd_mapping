from playwright.sync_api import sync_playwright
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThuocBietDuocDetail")

MAX_WAIT_PAGE = 90_000
MAX_WAIT_EL = 15_000


# --------------------------------------------------
# UTIL
# --------------------------------------------------
def safe_wait(sec=2):
    time.sleep(sec)


def safe_text(locator):
    try:
        txt = locator.inner_text()
        return txt.strip() if txt else None
    except:
        return None


# --------------------------------------------------
# BASIC INFO
# --------------------------------------------------
def extract_name(page):
    selectors = [
        "h1",
        "//h1[contains(@class,'font-bold')]"
    ]
    for s in selectors:
        try:
            el = page.locator(s).first
            el.wait_for(timeout=MAX_WAIT_EL)
            return safe_text(el)
        except:
            continue
    return None


def extract_registration_number(page):
    xpaths = [
        "//div[div[text()='Số đăng ký']]/div[contains(@class,'font-semibold')]",
        "//div[contains(text(),'Số đăng ký')]/following-sibling::div"
    ]
    for xp in xpaths:
        try:
            el = page.locator(xp).first
            el.wait_for(timeout=MAX_WAIT_EL)
            return safe_text(el)
        except:
            continue
    return None


def extract_dosage_form(page):
    xp = "//div[div[text()='Dạng bào chế']]/div[contains(@class,'font-semibold')]"
    try:
        el = page.locator(xp).first
        el.wait_for(timeout=MAX_WAIT_EL)
        return safe_text(el)
    except:
        return None


def extract_category(page):
    xp = "//div[div[text()='Danh mục']]//a"
    try:
        el = page.locator(xp).first
        el.wait_for(timeout=MAX_WAIT_EL)
        return safe_text(el)
    except:
        return None


# --------------------------------------------------
# INGREDIENTS
# --------------------------------------------------
def extract_ingredients_text(page):
    try:
        el = page.locator(".ingredient-content").first
        el.wait_for(timeout=MAX_WAIT_EL)
        return el.inner_text().strip()
    except:
        return None


def extract_active_ingredients_table(page):
    results = []
    try:
        rows = page.locator("#thanh-phan-hoat-chat tbody tr")
        for i in range(rows.count()):
            try:
                r = rows.nth(i)
                name = r.locator("td").nth(0).inner_text().strip()
                dose = r.locator("td").nth(1).inner_text().strip()
                results.append({
                    "name": name,
                    "dose": dose
                })
            except:
                continue
    except:
        pass
    return results or None


# --------------------------------------------------
# SECTION PARSER (H2 → UNTIL NEXT H2)
# --------------------------------------------------
def extract_section_text(page, start_id, stop_id=None):
    texts = []

    try:
        start = page.locator(f"#{start_id}").first
        start.wait_for(timeout=MAX_WAIT_EL)

        nodes = start.locator(
            "xpath=following-sibling::*"
        )

        for i in range(nodes.count()):
            node = nodes.nth(i)
            tag = node.evaluate("e => e.tagName")

            if tag == "H2" and stop_id and node.get_attribute("id") == stop_id:
                break

            texts.append(node.inner_text())

    except:
        return None

    return "\n".join(t.strip() for t in texts if t.strip())


# --------------------------------------------------
# MAIN EXTRACTOR
# --------------------------------------------------
def extract_drug_detail(url, headless=True):
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
            page.goto(url, timeout=MAX_WAIT_PAGE)
            safe_wait(8)

            data = {
                "url": url,
                "name": extract_name(page),
                "registration_number": extract_registration_number(page),
                "dosage_form": extract_dosage_form(page),
                "category": extract_category(page),
                "ingredients_text": extract_ingredients_text(page),
                "active_ingredients": extract_active_ingredients_table(page),
                "indications": extract_section_text(page, "section-1", "section-2"),
                "contraindications": extract_section_text(page, "section-2", "section-3"),
            }

            return data

        finally:
            browser.close()


# --------------------------------------------------
# TEST
# --------------------------------------------------
if __name__ == "__main__":
    url = "https://thuocbietduoc.com.vn/thuoc-48527/topsea-f.aspx"
    result = extract_drug_detail(url, headless=True)
    for k, v in result.items():
        print(f"\n{k.upper()}:\n{v}")
