from playwright.sync_api import sync_playwright, TimeoutError
import logging
from typing import Optional, List, Dict

# ======================================================
# CONFIG
# ======================================================
HEADLESS = True
GOTO_TIMEOUT = 60000
LOCATOR_TIMEOUT = 3000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RobustCrawler")

# ======================================================
# SAFE UTILS
# ======================================================
def safe_text(locator) -> Optional[str]:
    """Never crash when reading text"""
    try:
        text = locator.text_content()
        return text.strip() if text else None
    except Exception:
        return None

# ======================================================
# SAFE TABLE FIELD EXTRACTOR
# ======================================================
def extract_table_field_safe(page, label: str) -> Optional[str]:
    xpath = f"""
    //tr[td[contains(normalize-space(), '{label}')]]/td[last()]
    """

    try:
        locator = page.locator(xpath).first
        locator.wait_for(timeout=LOCATOR_TIMEOUT)
        return safe_text(locator)

    except TimeoutError:
        logger.warning(f"[MISS] Table field not found: {label}")
    except Exception as e:
        logger.error(f"[ERROR] Field '{label}': {e}")

    return None

# ======================================================
# SAFE SECTION EXTRACTOR (H2 → UNTIL NEXT H2)
# ======================================================
def extract_section_safe(page, keyword: str) -> List[str]:
    xpath = f"""
    //h2[contains(normalize-space(), '{keyword}')]/following-sibling::*[
        preceding-sibling::h2[1][contains(normalize-space(), '{keyword}')]
    ]
    """

    contents: List[str] = []

    try:
        nodes = page.locator(xpath)
        count = nodes.count()

        for i in range(count):
            try:
                text = nodes.nth(i).inner_text().strip()
                if text:
                    contents.append(text)
            except Exception:
                continue  # từng node lỗi cũng bỏ qua

    except Exception as e:
        logger.error(f"[ERROR] Section '{keyword}': {e}")

    return contents

# ======================================================
# CORE CRAWLER (ABSOLUTELY SAFE)
# ======================================================
def crawl_one(url: str) -> Dict:
    result = {
        "url": url,
        "error": None,
        "so_dang_ky": None,
        "dang_bao_che": None,
        "quy_cach": None,
        "hoat_chat": None,
        "chuyen_muc": None,
        "thanh_phan": [],
        "cong_dung": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        # ---------- GOTO (KHÔNG BAO GIỜ SẬP) ----------
        try:
            response = page.goto(url, timeout=GOTO_TIMEOUT)

            if not response:
                result["error"] = "NO_RESPONSE"
                logger.error("No response")
                return result

            if response.status >= 400:
                result["error"] = f"HTTP_{response.status}"
                logger.error(f"HTTP error {response.status}")
                return result

            page.wait_for_load_state("domcontentloaded")

        except TimeoutError:
            result["error"] = "TIMEOUT"
            logger.error("Page load timeout")
            return result

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Fatal page error: {e}")
            return result

        # ---------- EXTRACT (MỖI FIELD ĐỘC LẬP) ----------
        result["so_dang_ky"] = extract_table_field_safe(page, "Số đăng ký")
        result["dang_bao_che"] = extract_table_field_safe(page, "Dạng bào chế")
        result["quy_cach"] = extract_table_field_safe(page, "Quy cách đóng gói")
        result["hoat_chat"] = extract_table_field_safe(page, "Hoạt chất")
        result["chuyen_muc"] = extract_table_field_safe(page, "Chuyên mục")

        result["thanh_phan"] = extract_section_safe(page, "Thành phần")
        result["cong_dung"] = extract_section_safe(page, "Công dụng")

        browser.close()
        return result

# ======================================================
# RUN TEST
# ======================================================
if __name__ == "__main__":
    from pprint import pprint

    test_url = "https://trungtamthuoc.com/dewsoft-premia"
    data = crawl_one(test_url)

    pprint(data)
