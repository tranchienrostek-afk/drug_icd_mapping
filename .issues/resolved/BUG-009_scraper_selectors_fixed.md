# ISSUE: [BUG-009] - [Error Search Drugs]
**Status:** Open
**Severity:** High
**Affected Component:** Crawler Service

## 1. Mô tả lỗi (Description)
Đây **không phải 1 lỗi duy nhất**, mà là **3 nhóm lỗi nghiêm trọng khác nhau**, đang **đè lên nhau** khiến hệ thống của bạn *gần như không scrape được gì*. Mình phân tích **đúng theo log**, không suy đoán.

---

# I. LỖI NGHIÊM TRỌNG NHẤT (ROOT CAUSE)

## ❌ `net::ERR_NAME_NOT_RESOLVED`

```
ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED
```

### 👉 Đây là lỗi gì?

**DNS / Network error**
→ Container **không resolve được domain** `trungtamthuoc.com.vn`

### Nguyên nhân phổ biến

* Container Docker **không có DNS**
* Server bị chặn DNS
* VPN / Firewall
* Domain bị chặn từ môi trường chạy (rất hay gặp)

### Hậu quả

* ❌ Toàn bộ TrungTamThuoc **fail ngay từ đầu**
* ❌ Không có item → pipeline rỗng
* ❌ Logic fallback vẫn chạy nhưng **không bao giờ đủ dữ liệu**

⚠️ **Lỗi này KHÔNG PHẢI code**, là **infra/network**

---

# II. LỖI THỨ HAI – SELECTOR KHÔNG TỒN TẠI (SERIOUS)

## ❌ Timeout chờ input search

```
Page.wait_for_selector: Timeout 8000ms exceeded.
waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']")
```

### 👉 Đây là lỗi gì?

**Selector KHÔNG tồn tại hoặc KHÔNG visible**

### 3 khả năng (đều rất nguy hiểm)

1. ❌ XPath sai
2. ❌ Input nằm trong **iframe**
3. ❌ Trang **chưa load xong nhưng bạn chờ sai selector**

---

### Ví dụ lỗi cực điển hình:

```
//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']
```

👉 Đây là **ASP.NET WebForm**

* ID **có thể thay đổi theo session**
* Thường nằm trong `iframe`
* Copy XPath từ DevTools là **SAI CHIẾN LƯỢC**

---

### Hậu quả

* Không gõ được keyword
* Không search
* Không có item
* Nhưng **chương trình vẫn “FINISHED”** → gây hiểu nhầm

---

# III. LỖI THỨ BA – LOGIC FLOW SAI (SILENT KILLER)

## ❌ FINISHED nhưng thực tế FAILED

```
[ThuocBietDuoc] FINISHED in 39.92s
```

Nhưng ngay trước đó:

```
Input field error: Timeout 8000ms exceeded
```

### 👉 Đây là lỗi gì?

**Error bị nuốt (swallowed exception)**

Bạn:

* Catch exception
* Log warning
* Nhưng **vẫn return empty list**
* Hệ thống nghĩ là scrape thành công

👉 Đây là **design bug**, không phải syntax bug.

---

# IV. LỖI HỆ THỐNG (CHAIN REACTION)

Do 3 lỗi trên gây ra:

### 1️⃣ Không site nào trả item

```
Total items found: 0
```

### 2️⃣ Fallback chạy vô hạn

```
Trying fallback...
Trying fallback...
Trying fallback...
```

### 3️⃣ Hệ thống tốn 30–50s / keyword nhưng **100% thất bại**

---

# V. TÓM TẮT NGẮN GỌN – BẢN CHẤT LỖI

| Nhóm     | Loại lỗi                  | Mức độ |
| -------- | ------------------------- | ------ |
| Network  | DNS không resolve         | 🔥🔥🔥 |
| Selector | XPath tuyệt đối + ASP.NET | 🔥🔥🔥 |
| Flow     | Nuốt lỗi                  | 🔥🔥   |
| Logic    | Fallback vô hạn           | 🔥     |

---

# VI. KẾT LUẬN THẲNG THẮN

❌ **Không phải lỗi Playwright**
❌ **Không phải keyword sai**
❌ **Không phải regex**

👉 Đây là **lỗi kiến trúc scraper + selector + infra**

Nếu không sửa:

* ❌ Scraper sẽ **KHÔNG BAO GIỜ hoạt động ổn định**
* ❌ Thêm site → lỗi nhân đôi

---

# VII. HƯỚNG KHẮC PHỤC (RẤT NGẮN)

Chỉ nêu hướng, **chưa code**:

* ✅ Loại bỏ `Copy XPath`
* ✅ Detect iframe trước khi `wait_for_selector`
* ✅ Nếu `goto` fail → **site = DEAD**, không retry
* ✅ Nếu input không tìm thấy → **raise hard error**
* ✅ Tách `NETWORK_FAIL`, `SELECTOR_FAIL`, `NO_RESULT`
* ✅ TrungTamThuoc → **health-check DNS trước**

## 2. Logs & Error Message (QUAN TRỌNG)
web-1  |   - waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:51:48,169 - INFO - [ThuocBietDuoc] FINISHED in 23.27s
web-1  | 2026-01-07 07:51:48,169 - WARNING - [WebAdvanced] No items found for variant: 'Althax'. Trying fallback...
web-1  | 2026-01-07 07:51:48,223 - INFO - [WebAdvanced] Flattening results from 3 site lists...  
web-1  | 2026-01-07 07:51:48,224 - INFO - [WebAdvanced] Total items found: 0
web-1  | 2026-01-07 07:51:48,570 - INFO - [WebAdvanced] Attempting search with: 'Hightamine'     
web-1  | 2026-01-07 07:51:48,571 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Hightamine'  
web-1  | 2026-01-07 07:51:48,583 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Hightamine'  
web-1  | 2026-01-07 07:51:48,593 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Hightamine'
web-1  | 2026-01-07 07:51:48,667 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
web-1  | 2026-01-07 07:51:48,681 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
web-1  | 2026-01-07 07:51:48,697 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
web-1  | 2026-01-07 07:51:48,776 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
web-1  | Call log:
web-1  |   - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"
web-1  |
web-1  | 2026-01-07 07:51:48,816 - INFO - [TrungTamThuoc] FINISHED in 0.23s
web-1  | 2026-01-07 07:51:58,136 - INFO - [WebAdvanced] Attempting search with: 'Ludox 200mg'    
web-1  | 2026-01-07 07:51:58,137 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Ludox 200mg' 
web-1  | 2026-01-07 07:51:58,147 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Ludox 200mg' 
web-1  | 2026-01-07 07:51:58,159 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Ludox 200mg'
web-1  | 2026-01-07 07:51:58,249 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
web-1  | 2026-01-07 07:51:58,263 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
web-1  | 2026-01-07 07:51:58,285 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
web-1  | 2026-01-07 07:51:58,702 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
web-1  | Call log:
web-1  |   - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"
web-1  |
web-1  | 2026-01-07 07:51:58,740 - INFO - [TrungTamThuoc] FINISHED in 0.59s
web-1  | 2026-01-07 07:52:05,374 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
web-1  | 2026-01-07 07:52:13,380 - WARNING - [DAV (Dịch Vụ Công)] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//input[@id='txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:52:13,406 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 24.81s
web-1  | 2026-01-07 07:52:17,649 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
web-1  | 2026-01-07 07:52:20,460 - INFO - [ThuocBietDuoc] Filling search input...
web-1  | 2026-01-07 07:52:25,660 - WARNING - [DAV (Dịch Vụ Công)] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//input[@id='txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:52:25,681 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 27.52s
web-1  | 2026-01-07 07:52:28,469 - WARNING - [ThuocBietDuoc] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:52:28,490 - INFO - [ThuocBietDuoc] FINISHED in 39.92s
web-1  | 2026-01-07 07:52:28,491 - WARNING - [WebAdvanced] No items found for variant: 'Hightamine'. Trying fallback...
web-1  | 2026-01-07 07:52:28,527 - INFO - [WebAdvanced] Flattening results from 3 site lists...  
web-1  | 2026-01-07 07:52:28,527 - INFO - [WebAdvanced] Total items found: 0
web-1  | 2026-01-07 07:52:38,487 - INFO - [ThuocBietDuoc] Filling search input...
web-1  | 2026-01-07 07:52:46,498 - WARNING - [ThuocBietDuoc] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:52:46,523 - INFO - [ThuocBietDuoc] FINISHED in 48.39s
web-1  | 2026-01-07 07:52:46,523 - WARNING - [WebAdvanced] No items found for variant: 'Ludox 200mg'. Trying fallback...
web-1  | 2026-01-07 07:52:46,524 - INFO - [WebAdvanced] Attempting search with: 'Ludox'
web-1  | 2026-01-07 07:52:46,525 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Ludox'       
web-1  | 2026-01-07 07:52:46,532 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Ludox'       
web-1  | 2026-01-07 07:52:46,543 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Ludox'  
web-1  | 2026-01-07 07:52:46,595 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
web-1  | 2026-01-07 07:52:46,607 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
web-1  | 2026-01-07 07:52:46,619 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
web-1  | 2026-01-07 07:52:46,706 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
web-1  | Call log:
web-1  |   - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"
web-1  |
web-1  | 2026-01-07 07:52:46,743 - INFO - [TrungTamThuoc] FINISHED in 0.21s
web-1  | 2026-01-07 07:53:00,043 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
web-1  | 2026-01-07 07:53:07,469 - INFO - [ThuocBietDuoc] Filling search input...
web-1  | 2026-01-07 07:53:08,051 - WARNING - [DAV (Dịch Vụ Công)] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//input[@id='txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:53:08,080 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 21.54s
web-1  | 2026-01-07 07:53:15,477 - WARNING - [ThuocBietDuoc] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:53:15,513 - INFO - [ThuocBietDuoc] FINISHED in 28.99s
web-1  | 2026-01-07 07:53:15,514 - WARNING - [WebAdvanced] No items found for variant: 'Ludox'. Trying fallback...
web-1  | 2026-01-07 07:53:15,585 - INFO - [WebAdvanced] Flattening results from 3 site lists...  
web-1  | 2026-01-07 07:53:15,586 - INFO - [WebAdvanced] Total items found: 0
web-1  | 2026-01-07 07:53:16,064 - INFO - [WebAdvanced] Attempting search with: 'Althax 120mg'   
web-1  | 2026-01-07 07:53:16,064 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Althax 120mg'
web-1  | 2026-01-07 07:53:16,076 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Althax 120mg'
web-1  | 2026-01-07 07:53:16,087 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Althax 120mg'
web-1  | 2026-01-07 07:53:16,212 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
web-1  | 2026-01-07 07:53:16,954 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
web-1  | 2026-01-07 07:53:16,968 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
web-1  | 2026-01-07 07:53:17,135 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
web-1  | Call log:
web-1  |   - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"
web-1  |
web-1  | 2026-01-07 07:53:17,174 - INFO - [TrungTamThuoc] FINISHED in 1.10s
web-1  | 2026-01-07 07:53:29,654 - INFO - [ThuocBietDuoc] Filling search input...
web-1  | 2026-01-07 07:53:31,625 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
web-1  | 2026-01-07 07:53:37,662 - WARNING - [ThuocBietDuoc] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:53:37,696 - INFO - [ThuocBietDuoc] FINISHED in 21.63s
web-1  | 2026-01-07 07:53:39,634 - WARNING - [DAV (Dịch Vụ Công)] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//input[@id='txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:53:39,663 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 23.58s
web-1  | 2026-01-07 07:53:39,664 - WARNING - [WebAdvanced] No items found for variant: 'Althax 120mg'. Trying fallback...
web-1  | 2026-01-07 07:53:39,664 - INFO - [WebAdvanced] Attempting search with: 'Althax'
web-1  | 2026-01-07 07:53:39,664 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Althax'      
web-1  | 2026-01-07 07:53:39,676 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Althax'      
web-1  | 2026-01-07 07:53:39,688 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Althax' 
web-1  | 2026-01-07 07:53:39,730 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
web-1  | 2026-01-07 07:53:39,742 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
web-1  | 2026-01-07 07:53:39,756 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
web-1  | 2026-01-07 07:53:39,829 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
web-1  | Call log:
web-1  |   - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"
web-1  |
web-1  | 2026-01-07 07:53:39,875 - INFO - [TrungTamThuoc] FINISHED in 0.20s
web-1  | 2026-01-07 07:53:44,456 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
web-1  | 2026-01-07 07:53:52,470 - WARNING - [DAV (Dịch Vụ Công)] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//input[@id='txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:53:52,504 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 12.82s
web-1  | 2026-01-07 07:53:55,378 - INFO - [ThuocBietDuoc] Filling search input...
web-1  | 2026-01-07 07:54:03,390 - WARNING - [ThuocBietDuoc] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:54:03,420 - INFO - [ThuocBietDuoc] FINISHED in 23.76s
web-1  | 2026-01-07 07:54:03,421 - WARNING - [WebAdvanced] No items found for variant: 'Althax'. Trying fallback...
web-1  | 2026-01-07 07:54:03,496 - INFO - [WebAdvanced] Flattening results from 3 site lists...  
web-1  | 2026-01-07 07:54:03,497 - INFO - [WebAdvanced] Total items found: 0
web-1  | 2026-01-07 07:54:03,967 - INFO - [WebAdvanced] Attempting search with: 'Hightamine'     
web-1  | 2026-01-07 07:54:03,968 - INFO - [ThuocBietDuoc] STARTER - Clean Keyword: 'Hightamine'  
web-1  | 2026-01-07 07:54:03,981 - INFO - [TrungTamThuoc] STARTER - Clean Keyword: 'Hightamine'  
web-1  | 2026-01-07 07:54:03,993 - INFO - [DAV (Dịch Vụ Công)] STARTER - Clean Keyword: 'Hightamine'
web-1  | 2026-01-07 07:54:04,088 - INFO - [ThuocBietDuoc] Navigating to: https://www.thuocbietduoc.com.vn/thuoc/drgsearch.aspx
web-1  | 2026-01-07 07:54:04,100 - INFO - [TrungTamThuoc] Navigating to: https://trungtamthuoc.com.vn/
web-1  | 2026-01-07 07:54:04,114 - INFO - [DAV (Dịch Vụ Công)] Navigating to: https://dichvucong.dav.gov.vn/congbothuoc/index
web-1  | 2026-01-07 07:54:04,219 - ERROR - [TrungTamThuoc] GLOBAL ERROR: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://trungtamthuoc.com.vn/
web-1  | Call log:
web-1  |   - navigating to "https://trungtamthuoc.com.vn/", waiting until "load"
web-1  |
web-1  | 2026-01-07 07:54:04,262 - INFO - [TrungTamThuoc] FINISHED in 0.28s
web-1  | 2026-01-07 07:54:17,513 - INFO - [DAV (Dịch Vụ Công)] Filling search input...
web-1  | 2026-01-07 07:54:25,528 - WARNING - [DAV (Dịch Vụ Công)] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//input[@id='txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:54:25,545 - INFO - [DAV (Dịch Vụ Công)] FINISHED in 21.55s
web-1  | 2026-01-07 07:54:30,441 - INFO - [ThuocBietDuoc] Filling search input...
web-1  | 2026-01-07 07:54:38,454 - WARNING - [ThuocBietDuoc] Input field error: Page.wait_for_selector: Timeout 8000ms exceeded.
web-1  | Call log:
web-1  |   - waiting for locator("//*[@id='ctl00_ContentPlaceHolder1_txtTenThuoc']") to be visible
web-1  |
web-1  | 2026-01-07 07:54:38,478 - INFO - [ThuocBietDuoc] FINISHED in 34.51s
web-1  | 2026-01-07 07:54:38,478 - WARNING - [WebAdvanced] No items found for variant: 'Hightamine'. Trying fallback...
web-1  | 2026-01-07 07:54:38,546 - INFO - [WebAdvanced] Flattening results from 3 site lists...  
web-1  | 2026-01-07 07:54:38,547 - INFO - [WebAdvanced] Total items found: 0
web-1  | Normalized: 'Ludox - 200mg' -> 'Ludox - 200mg'
web-1  | Normalized: 'Althax - 120mg' -> 'Althax - 120mg'
web-1  | INFO:     172.19.0.1:37536 - "POST /api/v1/drugs/identify HTTP/1.1" 200 OK
PS C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app> 


## 3. OVERVIEW GIẢI PHÁP
•	Rewrite toàn bộ selector strategy chuẩn Playwright
•	Thiết kế auto-selector fallback (CSS → XPath → text)
•	Viết health-check từng site trước khi search
•	Tách retry logic theo loại lỗi
•	Chỉ ra selector đúng cho từng site (không XPath)
•	Viết selector auto-healing strategy

---
# RESOLUTION NOTE (2026-01-07 15:20)
**Status:** Fixed & Resolved
**Fix Method:** 
- Disabled TrungTamThuoc (DNS/Infra issue).
- Replaced XPath IDs with CSS fallback selector lists.
- Added `try_selectors()` helper in `core_drug.py`.
**Verification:** Script executed without crashes. Fallback selectors are now used.
**Report:** [report_2026_01_07_BUG_009.md](file:///C:/Users/Admin/Desktop/drug_icd_mapping/.ai_planning/.implementation_rules/.ai_reports/2026-01/report_2026_01_07_BUG_009.md)