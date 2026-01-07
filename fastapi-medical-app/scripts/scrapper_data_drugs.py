import pandas as pd
from playwright.sync_api import sync_playwright
import time

# --- CẤU HÌNH ---
URL_TARGET = "https://thuocbietduoc.com.vn/thuoc/drgsearch.aspx"
MAX_PAGES = 2  # Số trang muốn cào thử nghiệm
OUTPUT_FILE = "dulieu_thuoc_playwright.csv"

def clean_text(locator):
    """Hàm hỗ trợ lấy text và làm sạch khoảng trắng thừa"""
    try:
        if locator.count() > 0:
            return locator.first.inner_text().strip()
        return ""
    except Exception:
        return ""

def run_scraper():
    all_drugs = []

    with sync_playwright() as p:
        # Khởi tạo trình duyệt (headless=False để bạn nhìn thấy nó chạy)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"--- Bắt đầu truy cập: {URL_TARGET} ---")
        page.goto(URL_TARGET)
        
        # Chờ trang load xong element chính
        page.wait_for_selector('section')

        current_page = 1
        while current_page <= MAX_PAGES:
            print(f"\n>> Đang xử lý TRANG {current_page}")

            # 1. Lấy danh sách link sản phẩm trên trang hiện tại
            # XPath trỏ vào thẻ <a> của từng thuốc
            product_locator = page.locator('xpath=/html/body/main/section[3]/div/div/div/div[2]/div/div/a')
            
            # Đợi danh sách load
            product_locator.first.wait_for()
            
            # Lấy tất cả href (đường dẫn) để không cần click đi click lại trang danh sách
            # Cách này nhanh hơn và ổn định hơn việc Back/Forward
            count = product_locator.count()
            links = []
            for i in range(count):
                url = product_locator.nth(i).get_attribute('href')
                if url:
                    links.append(url)
            
            print(f"   Tìm thấy {len(links)} thuốc. Bắt đầu cào chi tiết...")

            # 2. Duyệt qua từng link thuốc (Mở tab mới xử lý cho nhanh)
            for link in links:
                try:
                    # Mở trang chi tiết thuốc
                    detail_page = context.new_page()
                    # Apply stealth immediately - REMOVED due to import error
                    # stealth_sync(detail_page)
                    detail_page.goto(link)
                    
                    # --- ROBUST SELECTORS (MẸO: Tìm theo Text thay vì đếm div) ---
                    
                    # 1. Tên thuốc (Luôn là thẻ H1 duy nhất)
                    name_loc = detail_page.locator('h1')
                    
                    # 2. Số đăng ký (Tìm div chứa chữ "Số đăng ký" -> lấy div bên cạnh)
                    sdk_loc = detail_page.locator("xpath=//div[contains(text(), 'Số đăng ký')]/following-sibling::div")
                    
                    # 3. Hoạt chất (Tìm div chứa chữ "Hoạt chất" hoặc class .ingredient-content)
                    # Web này dùng class .ingredient-content cho khung hoạt chất, rất ổn định
                    hc_loc = detail_page.locator('.ingredient-content')
                    
                    # 4. Dạng bào chế (Tương tự SĐK)
                    dbc_loc = detail_page.locator("xpath=//div[contains(text(), 'Dạng bào chế')]/following-sibling::div")
                    
                    # 5. Danh mục / Nhóm thuốc
                    dm_loc = detail_page.locator("xpath=//div[contains(text(), 'Nhóm thuốc')]/following-sibling::div")
                    
                    # 6. Hàm lượng (Thường nằm cùng Hoạt chất hoặc trong bảng)
                    # Nếu không tìm thấy, lấy tạm text của hoạt chất
                    hl_loc = detail_page.locator("xpath=//div[contains(text(), 'Hàm lượng')]/following-sibling::div")
                    
                    # 7. Nội dung điều trị
                    # Tìm thẻ có id="chi-dinh" hoặc thẻ chứa text "Chỉ định"
                    content_loc = detail_page.locator('#chi-dinh')
                    if content_loc.count() == 0:
                         content_loc = detail_page.locator("xpath=//h2[contains(text(), 'Chỉ định')]/following-sibling::div")

                    # Lấy dữ liệu
                    ten_thuoc = clean_text(name_loc)
                    so_dang_ky = clean_text(sdk_loc)
                    hoat_chat = clean_text(hc_loc)
                    dang_bao_che = clean_text(dbc_loc)
                    danh_muc = clean_text(dm_loc)
                    ham_luong = clean_text(hl_loc)
                    noi_dung = clean_text(content_loc)

                    # LOGIC BỔ SUNG: Nếu SĐK rỗng, thử tìm trong title hoặc body
                    if not so_dang_ky:
                         # Fallback: Sometimes SDK is concatenated in other fields
                         pass

                    # Ghi nhận dữ liệu
                    record = {
                        "so_dang_ky": so_dang_ky,       # KHOÁ CHÍNH
                        "ten_thuoc": ten_thuoc,
                        "hoat_chat": hoat_chat,
                        "noi_dung_dieu_tri": noi_dung,  # DỮ LIỆU ĐỂ MAP ICD
                        "ma_icd": "",                   # Placeholder
                        "trang_thai_xac_nhan": "Pending",
                        "dang_bao_che": dang_bao_che,
                        "danh_muc": danh_muc,
                        "ham_luong": ham_luong,
                        "url_nguon": link
                    }
                    
                    all_drugs.append(record)
                    print(f"   -> [OK] {ten_thuoc} | SĐK: {so_dang_ky}")
                    
                    detail_page.close()

                except Exception as e:
                    print(f"   -> [LỖI] {link}: {e}")
                    if 'detail_page' in locals(): detail_page.close()

            # 3. Chuyển trang (Pagination)
            # XPath nút Next trang 2: /html/body/main/section[3]/div/div/div/div[3]/nav/div/div[2]/span/a[1]
            # Logic: Tìm thẻ 'a' chứa text trang tiếp theo hoặc nút 'Next'
            if current_page < MAX_PAGES:
                try:
                    # Tìm nút bấm chuyển sang trang (current_page + 1)
                    # Sử dụng selector thông minh của Playwright tìm theo text hoặc href
                    next_page_num = current_page + 1
                    
                    # Cách 1: Tìm theo href chứa page=... (Chính xác nhất)
                    # page.click(f"//a[contains(@href, 'page={next_page_num}')]")
                    
                    # Cách 2: Dùng đúng XPath bạn cung cấp (chỉ đúng cho trang 1->2, cẩn thận các trang sau)
                    # Để code chạy tự động nhiều trang, tôi dùng logic tìm href
                    next_btn = page.locator(f"//a[contains(@href, 'page={next_page_num}')]")
                    
                    if next_btn.count() > 0:
                        print(f"   >> Chuyển sang trang {next_page_num}...")
                        next_btn.first.click()
                        # Chờ URL thay đổi hoặc element trang mới xuất hiện
                        page.wait_for_timeout(3000) 
                        current_page += 1
                    else:
                        print("   Không tìm thấy nút Next. Dừng lại.")
                        break
                except Exception as e:
                    print(f"   Lỗi chuyển trang: {e}")
                    break
            else:
                break

        browser.close()

    # 4. Lưu file
    df = pd.DataFrame(all_drugs)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\nHoàn tất! Dữ liệu đã lưu tại: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_scraper()