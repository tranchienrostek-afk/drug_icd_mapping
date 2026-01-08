# ISSUE: [BUG-007] - Không thể search được thuốc
**Status:** Open
**Severity:** High
**Affected Component:** scrapper, playwright, xpath, selector, fail

## 1. Mô tả lỗi (Description)
I. LỖI CHẾT NGƯỜI (Runtime / Logic Error)
❌ 1. Field_Selectors trộn None và dict
"Field_Selectors": [
    None,
    {...},
    {...}
]

Vấn đề

Code scraper chắc chắn có đoạn:

for field, xpath in config["Field_Selectors"].items():


→ Crash ngay khi gặp None.

Hậu quả

DAV (priority 99) sẽ làm sập toàn bộ pipeline

Không thể generic hóa scraper

Kết luận

👉 Không bao giờ được dùng None ở đây

❌ 2. XPath_Link_ChiTiet = "NO_LINK" là giá trị không hợp lệ
"XPath_Link_ChiTiet": [
    "NO_LINK", 
    ".", 
    "."
]

Vấn đề

"NO_LINK" không phải XPath

Scraper sẽ:

hoặc cố .querySelector("NO_LINK") → lỗi

hoặc check truthy → xử lý sai luồng

Hậu quả

Phải hard-code if/else cho DAV

Mất tính cấu hình hóa

Chuẩn đúng

Dùng None

hoặc empty string ""

hoặc flag riêng: Has_Detail_Page: False

❌ 3. XPath tuyệt đối (/html/body/...) → gãy 100%

Ví dụ:

"/html/body/div[4]/div/div[1]/div/div/div[2]/div[1]/div/input[2]"

Vấn đề

Chỉ cần:

thêm 1 banner

đổi layout A/B
→ XPath toang ngay

Mức độ

🔥🔥🔥 CỰC KỲ NGUY HIỂM

Nguyên tắc scraper sống sót

❌ Tuyệt đối XPath

✅ Relative XPath + attribute + contains()

❌ 4. XPath union (|) trả về NHIỀU NODE nhưng code thường lấy 1

Ví dụ:

//*[@id="cscontentdetail"]/div/div/div/strong/a | //*[@id="cscontentdetail"]/div/div/strong/a

Vấn đề

XPath này có thể match:

0 node

1 node

N node

Nếu code:
element = page.locator(xpath).text_content()


→ lấy node đầu tiên ngẫu nhiên

Hậu quả

Dữ liệu sai ngầm (silent data corruption)

Audit không phát hiện

II. LỖI KIẾN TRÚC (Design Flaw)
❌ 5. HanhDong_TimKiem trộn enum và XPath
"HanhDong_TimKiem": [
    "xpath=...",
    "ENTER",
    "ENTER"
]

Vấn đề

1 field nhưng chứa:

XPath

keyword hành vi

Code xử lý sẽ thành:
if value == "ENTER": ...
elif value.startswith("xpath="): ...


👉 Code smell cấp độ cao

Chuẩn đúng

Tách rõ:

Search_Action_Type: CLICK | ENTER
Search_Action_XPath: ...

❌ 6. Max_Item không có ngữ nghĩa rõ ràng
"Max_Item": [1, 2, 2]

Không rõ:

Giới hạn số kết quả search?

Giới hạn số item crawl?

Giới hạn số page?

Hậu quả

Mỗi dev hiểu 1 kiểu

Bug logic rất khó trace

❌ 7. UuTien đảo logic với STT
df.sort_values(by='UuTien')

Vấn đề

STT tồn tại nhưng không có ý nghĩa

UuTien nhỏ là ưu tiên cao → ngược trực giác

Hậu quả

Rất dễ bug khi thêm site mới

Người đọc config hiểu sai

III. LỖI DỮ LIỆU / SCRAPING SEMANTIC
❌ 8. XPath ham_luong trả về cả <table>
//*[@id="pro-mo-ta-noi-dung"]/table

Vấn đề

Scraper thường lấy .text_content()
→ toàn bộ bảng bị nhét vào 1 field

Hậu quả

Không parse được

Dữ liệu bẩn không thể normalize

❌ 9. chi_dinh XPath quá rộng
//div[contains(@class, 'cs-content')]

Vấn đề

Có thể chứa:

chỉ định

chống chỉ định

mô tả

quảng cáo

Hậu quả

Field chi_dinh bị ô nhiễm nội dung

❌ 10. Thiếu chuẩn hóa output (schema drift)

Không site nào đảm bảo:

hoat_chat là text / list?

ham_luong là string / table?

danh_muc là 1 hay nhiều?

👉 Chưa có contract dữ liệu

IV. LỖI VẬN HÀNH / BẢO TRÌ
❌ 11. Không có version cho từng site

Docstring ghi:

Updated: 2026-01-07 - Specific XPaths from BUG-001


Nhưng:

Không site-level version

Không changelog theo TenTrang

👉 Không thể rollback

❌ 12. Không có cơ chế disable site

Nếu 1 site:

đổi layout

chặn bot

→ toàn pipeline fail

❌ 13. get_icd_web_config() không cùng schema

Khác hẳn drug config:

field tên khác

logic khác

không tái sử dụng pipeline

👉 Hai hệ thống scraper ngầm tách rời

V. LỖI TRIẾT LÝ (CỰC KỲ NGUY HIỂM)
❌ 14. Config đang “giấu code” trong dữ liệu

XPath phức tạp + union + hard logic → thực chất là code nhưng:

không test được

không lint

không validate

👉 Đây là anti-pattern kinh điển của scraper chết yểu

TỔNG KẾT – PHÁN QUYẾT THẲNG
Mức	Nhận định
Độ ổn định	❌ Rất thấp
Khả năng mở rộng	❌ Gần như không
Audit dữ liệu	❌ Không kiểm soát
Production-ready	❌ Tuyệt đối chưa

## 2. Logs & Error Message (QUAN TRỌNG)
2026-01-07 06:57:15,017 - INFO - [WebAdvanced] Attempting search with: 'Atifertil Woman'
2026-01-07 06:57:15,017 - INFO - [WebAdvanced] Attempting search with: 'Atifertil Woman'
2026-01-07 06:57:15,027 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Atifertil Woman'
2026-01-07 06:57:15,027 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Atifertil Woman'
2026-01-07 06:57:15,048 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Atifertil Woman'
2026-01-07 06:57:15,048 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Atifertil Woman'
2026-01-07 06:57:15,061 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Atifertil Woman'
2026-01-07 06:57:15,061 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Atifertil Woman'
2026-01-07 06:57:15,272 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
2026-01-07 06:57:15,272 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
2026-01-07 06:57:15,287 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
2026-01-07 06:57:15,287 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
2026-01-07 06:57:15,300 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
2026-01-07 06:57:15,300 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
2026-01-07 06:57:16,337 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
Call log:
  - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"

2026-01-07 06:57:16,337 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
Call log:
  - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"

2026-01-07 06:57:16,518 - INFO - [TrungTamThuoc] Screenshot saved: app/logs/screenshots/TrungTamThuoc_global_error_1767769036.png
2026-01-07 06:57:16,518 - INFO - [TrungTamThuoc] Screenshot saved: app/logs/screenshots/TrungTamThuoc_global_error_1767769036.png
2026-01-07 06:57:16,558 - INFO - [TrungTamThuoc] FINISHED in 1.51s
2026-01-07 06:57:16,558 - INFO - [TrungTamThuoc] FINISHED in 1.51s
2026-01-07 06:57:20,391 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
2026-01-07 06:57:20,391 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
2026-01-07 06:57:20,757 - INFO - [DAV (Dịch Vụ Công)] Search triggered.
2026-01-07 06:57:20,757 - INFO - [DAV (Dịch Vụ Công)] Search triggered.
2026-01-07 06:57:22,808 - INFO - [DAV (Dịch Vụ Công)] Found 10 items.
2026-01-07 06:57:22,808 - INFO - [DAV (Dịch Vụ Công)] Found 10 items.
2026-01-07 06:57:22,809 - INFO - [DAV (Dịch Vụ Công)] Item 1: Link found: N/A
2026-01-07 06:57:22,809 - INFO - [DAV (Dịch Vụ Công)] Item 1: Link found: N/A
2026-01-07 06:57:22,845 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 7.78s
2026-01-07 06:57:22,845 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 7.78s
2026-01-07 06:57:50,645 - INFO - [ThuocBietDuoc] Filling search input...
2026-01-07 06:57:50,645 - INFO - [ThuocBietDuoc] Filling search input...
2026-01-07 06:57:50,745 - INFO - [ThuocBietDuoc] Search triggered.
2026-01-07 06:57:50,745 - INFO - [ThuocBietDuoc] Search triggered.
2026-01-07 06:58:02,757 - WARNING - [ThuocBietDuoc] Primary container not found. Trying Smart Fallback...
2026-01-07 06:58:02,757 - WARNING - [ThuocBietDuoc] Primary container not found. Trying Smart Fallback...
2026-01-07 06:58:05,366 - INFO - [ThuocBietDuoc] Fallback 2: Searching by Keyword Link text...
2026-01-07 06:58:05,366 - INFO - [ThuocBietDuoc] Fallback 2: Searching by Keyword Link text...
2026-01-07 06:58:05,390 - WARNING - [ThuocBietDuoc] All fallbacks failed.
2026-01-07 06:58:05,390 - WARNING - [ThuocBietDuoc] All fallbacks failed.
2026-01-07 06:58:08,956 - INFO - [ThuocBietDuoc] FINISHED in 53.93s
2026-01-07 06:58:08,956 - INFO - [ThuocBietDuoc] FINISHED in 53.93s
2026-01-07 06:58:08,958 - INFO - [WebAdvanced] Found potential results for variant: 'Atifertil Woman'
2026-01-07 06:58:08,958 - INFO - [WebAdvanced] Found potential results for variant: 'Atifertil Woman'
2026-01-07 06:58:09,007 - INFO - [WebAdvanced] Flattening results from 3 site lists...
2026-01-07 06:58:09,007 - INFO - [WebAdvanced] Flattening results from 3 site lists...
2026-01-07 06:58:09,009 - INFO - [WebAdvanced] Total items found: 1
2026-01-07 06:58:09,009 - INFO - [WebAdvanced] Total items found: 1
2026-01-07 06:58:09,010 - INFO - [WebAdvanced] Candidates with SDK: 0
2026-01-07 06:58:09,010 - INFO - [WebAdvanced] Candidates with SDK: 0
2026-01-07 06:58:09,011 - WARNING - [WebAdvanced] No SDK found. Returning best item without SDK.
2026-01-07 06:58:09,011 - WARNING - [WebAdvanced] No SDK found. Returning best item without SDK.

## 3. ĐỀ XUẤT GIẢI PHÁP

## I. Giải pháp kiến trúc (BẮT BUỘC)

* Chuẩn hoá **schema config scraper** (không cho phép giá trị mơ hồ)
* Tách rõ **Config (dữ liệu)** và **Logic (code)**
* Mỗi website = **1 module config độc lập**
* Không dùng `None` trong cấu trúc lặp → dùng object rỗng `{}` hoặc flag
* Bỏ hoàn toàn XPath tuyệt đối (`/html/body/...`)

---

## II. Giải pháp cấu trúc dữ liệu

* Thay `Field_Selectors: None` → `{}` hoặc `{"enabled": false}`
* Thêm cờ:

  * `Has_Detail_Page: true/false`
  * `Has_Search_Button: true/false`
* Thay `"NO_LINK"` bằng:

  * `XPath_Link_ChiTiet: null`
* Chuẩn hoá kiểu dữ liệu output:

  * `hoat_chat`: list
  * `ham_luong`: list `{chat, ham_luong}`
  * `danh_muc`: list

---

## III. Giải pháp XPath & Selector

* Chuyển XPath tuyệt đối → XPath tương đối + attribute
* Mỗi XPath chỉ match **1 node có chủ đích**
* Không dùng union `|` trong config
  → tách thành **fallback list**
* Tách:

  * `Primary_XPath`
  * `Fallback_XPaths: []`
* Với table → chỉ định rõ cell cần lấy

---

## IV. Giải pháp hành động tìm kiếm

* Tách `HanhDong_TimKiem` thành:

  * `Search_Action_Type: ENTER | CLICK`
  * `Search_Action_XPath`
* Không trộn keyword và XPath trong cùng field
* Validate action trước khi chạy scraper

---

## V. Giải pháp kiểm soát dữ liệu (RẤT QUAN TRỌNG)

* Áp dụng **Data Contract** cho output
* Validate:

  * Field rỗng
  * Field dài bất thường
  * HTML chưa parse
* Log **raw + parsed value**
* Gắn `source_site`, `source_xpath` cho từng field

---

## VI. Giải pháp vận hành & độ bền

* Thêm:

  * `Enabled: true/false` cho từng site
* Thêm version riêng cho từng website
* Có cơ chế skip site khi:

  * XPath fail
  * Bị block
* Cho phép override config không cần sửa code

---

## VII. Giải pháp test & audit

* Viết **config validator**:

  * Kiểm tra XPath hợp lệ
  * Không cho `None`
  * Không cho XPath tuyệt đối
* Snapshot HTML test cho mỗi site
* Test:

  * selector tồn tại
  * selector trả về đúng 1 node
* Log đầy đủ để **truy vết lỗi sau này**

---

## VIII. Giải pháp mở rộng lâu dài

* Chuẩn hoá pipeline:

  * Search → List → Detail → Parse → Normalize
* Mỗi bước có log & timeout riêng
* Tách scraper & parser thành 2 layer
* Chuẩn bị sẵn adapter cho site mới

---

## IX. Giải pháp ICD scraper

* Chuẩn hoá ICD config **cùng schema với drug**
* Không viết pipeline riêng
* Áp dụng chung validator & parser

---

## Chốt hạ (rất quan trọng)

* ❌ Không vá lỗi lẻ
* ❌ Không thêm XPath cho “chạy được”
* ✅ **Refactor có kiểm soát**
* ✅ **Ưu tiên độ bền hơn tốc độ**

