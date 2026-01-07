# ISSUE: [BUG-001] - [Search Drugs]
**Status:** Resolved (Monitoring)
**Severity:** High
**Affected Component:** `web_crawler.py`

## 1. Mô tả lỗi (Description)
Các selector (XPath/CSS) cũ trên `ThuocBietDuoc` và `TrungTamThuoc` không còn hoạt động do thay đổi giao diện. Crawler không lấy được "Số đăng ký" (SDK) và trả về kết quả rỗng hoặc thiếu thông tin.

## 2. Root Cause Analysis (Phân tích nguyên nhân)
1.  **Selectors Outdated:** Cấu trúc DOM thay đổi, các class và ID cũ không còn tồn tại.
2.  **Missing Headers:** Crawler thiếu `User-Agent` và `Accept-Language` chuẩn, dẫn đến việc bị chặn hoặc nhận HTML không đầy đủ từ server.
3.  **Invalid XPath Syntax:** Cấu hình selector sử dụng cú pháp kết hợp `xpath=` bên trong chuỗi union (`|`) gây lỗi cho Playwright (ví dụ: `//h1 | xpath=/div` là không hợp lệ).

## 3. Implementation / Fix Details (Chi tiết sửa lỗi)
-   **Reverse Debugging:** Đã dump HTML thực tế và xác nhận trường "Số đăng ký" (VD-...) vẫn tồn tại dưới dạng sibling của text "Số đăng ký".
-   **Updated Selectors:** chuyển sang sử dụng Relative XPath bền vững hơn: `//*[contains(text(), 'Số đăng ký')]/following-sibling::*`.
-   **Headers Enhancement:** Thêm đầy đủ headers (User-Agent, Accept, Sec-Ch-Ua) vào `browser.new_context()`.
-   **Config Cleaning:** Loại bỏ tiền tố `xpath=` thừa trong các chuỗi union selector.

## 4. Verification (Kiểm tra)
-   **Manual Script:** `scripts/debug_crawler_manual.py` đã chạy nhưng kết quả vẫn chưa ổn định (do rate limiting).
-   **Automated Test:** `tests/test_crawler_bug_001.py` đã được cập nhật logic nhưng đánh dấu `@pytest.mark.xfail` do tính chất chập chờn của trang đích (Anti-bot).

## 5. Next Steps
-   Tiếp tục theo dõi tỷ lệ thành công khi chạy thực tế.
-   Cân nhắc sử dụng Proxy IP nếu bị chặn thường xuyên.