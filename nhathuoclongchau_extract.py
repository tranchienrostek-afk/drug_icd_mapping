import os
from playwright.sync_api import sync_playwright, TimeoutError
from urllib.parse import urljoin

HEADLESS_ENV = os.getenv("HEADLESS", "true").lower() == "true"


def safe_text(locator):
    try:
        if locator.count() > 0:
            return locator.first.inner_text().strip()
    except:
        pass
    return None


def extract_by_label(page, label_text):
    try:
        blocks = page.locator("div.flex").filter(
            has=page.locator(f'p:text("{label_text}")')
        )
        if blocks.count() == 0:
            return None

        value = blocks.first.locator(
            "div.flex-1 span, div.flex-1 p"
        )
        return safe_text(value)
    except:
        return None


def click_view_more_if_exists(page):
    try:
        btn = page.locator('p:text("Xem thêm")')
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_timeout(1500)
    except:
        pass


def extract_section_text(page, section_id):
    try:
        sec = page.locator(f"#{section_id}")
        if sec.count() == 0:
            return None
        return sec.inner_text().strip()
    except:
        return None


def extract_longchau_detail(url):
    data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS_ENV,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120 Safari/537.36"
            ),
            locale="vi-VN"
        )
        page = context.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path="longchau_detail_start.png")

        # --- BẤM XEM THÊM NẾU CÓ ---
        click_view_more_if_exists(page)

        # --- TÊN THUỐC ---
        data["ten_thuoc"] = safe_text(
            page.locator('h1[data-test="product_name"]')
        )

        # --- TÊN PHỤ ---
        data["ten_phu"] = safe_text(
            page.locator('p.lc-tit')
        )

        # --- CÁC TRƯỜNG DẠNG LABEL ---
        data["danh_muc"] = extract_by_label(page, "Danh mục")
        data["so_dang_ky"] = extract_by_label(page, "Số đăng ký")
        data["dang_bao_che"] = extract_by_label(page, "Dạng bào chế")
        data["thanh_phan"] = extract_by_label(page, "Thành phần")

        # --- NỘI DUNG CHI TIẾT ---
        data["mo_ta_san_pham"] = extract_section_text(page, "detail-content-0")
        data["cong_dung"] = extract_section_text(page, "detail-content-2")
        data["tac_dung_phu"] = extract_section_text(page, "detail-content-4")

        # --- CHỈ ĐỊNH (có thể là h3 con) ---
        try:
            chi_dinh = page.locator(
                '#detail-content-1 h3:text("Chỉ định")'
            ).locator("xpath=following-sibling::*")
            data["chi_dinh"] = safe_text(chi_dinh)
        except:
            data["chi_dinh"] = None

        browser.close()

    return data


if __name__ == "__main__":
    test_url = "https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang/vien-uong-c-500mg-natures-bounty-100-vien.html"
    result = extract_longchau_detail(test_url)

    for k, v in result.items():
        print(f"\n=== {k.upper()} ===")
        print(v)
