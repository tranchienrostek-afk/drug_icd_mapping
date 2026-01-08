import os
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError

BASE_URL = "https://nhathuoclongchau.com.vn"
SEARCH_TIMEOUT = 20000  # ms

HEADLESS_ENV = os.getenv("HEADLESS", "true").lower() == "true"


def search_drug(keyword: str, max_links: int = 2):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS_ENV,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="vi-VN"
        )

        page = context.new_page()
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_timeout(3000)

        # --- 1. TÌM Ô SEARCH ---
        search_input = page.locator(
            'input[name="search"]'
        )
        search_input.wait_for(timeout=SEARCH_TIMEOUT)

        # --- 2. NHẬP TỪ KHÓA + ENTER ---
        search_input.fill(keyword)
        page.keyboard.press("Enter")

        # --- 3. CHỜ KẾT QUẢ ---
        try:
            page.wait_for_selector(
                '#category-page__products-section a[href$=".html"]',
                timeout=SEARCH_TIMEOUT
            )
        except TimeoutError:
            print("❌ Không tìm thấy kết quả")
            browser.close()
            return results

        page.wait_for_timeout(2000)

        # --- 4. LẤY LINK ---
        anchors = page.locator(
            '#category-page__products-section a[href$=".html"]'
        )

        count = anchors.count()

        for i in range(count):
            if len(results) >= max_links:
                break

            href = anchors.nth(i).get_attribute("href")
            if not href:
                continue

            full_url = urljoin(BASE_URL, href)

            # chống trùng
            if full_url not in results:
                results.append(full_url)

        browser.close()

    return results


if __name__ == "__main__":
    keyword = "Maca"
    links = search_drug(keyword)

    print("\n✅ LINK TÌM ĐƯỢC:")
    for link in links:
        print(link)
