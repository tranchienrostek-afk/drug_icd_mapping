
from playwright.sync_api import sync_playwright
import time

URL = "https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print(f"Navigating to {URL}...")
        page.goto(URL)
        
        print("Waiting for search input...")
        # Try to find any input
        try:
            page.wait_for_selector("input", timeout=10000)
            inputs = page.locator("input").all()
            print(f"Found {len(inputs)} inputs:")
            for i, inp in enumerate(inputs):
                try:
                    attr_name = inp.get_attribute("name")
                    attr_id = inp.get_attribute("id")
                    attr_placeholder = inp.get_attribute("placeholder")
                    is_visible = inp.is_visible()
                    print(f"  [{i}] Name: {attr_name}, ID: {attr_id}, Placeholder: {attr_placeholder}, Visible: {is_visible}")
                except Exception as e:
                    print(f"  [{i}] Error reading attributes: {e}")
        except Exception as e:
            print(f"Error finding inputs: {e}")

        # specific check for config selectors
        print("\nChecking Config Selectors:")
        selectors = [
            "#search-form input[name='key']",
            "#search-input",
            "input[name='key']",
            "#txtSearch" 
        ]
        for sel in selectors:
            count = page.locator(sel).count()
            print(f"  Selector '{sel}': Found {count}")

        browser.close()

if __name__ == "__main__":
    run()
