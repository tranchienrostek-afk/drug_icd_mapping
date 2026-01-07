# ISSUE: BUG-005 - Bộ chọn (Selectors) Web Crawler bị lỗi thời
**Status:** Resolved
**Severity:** Critical
**Affected Component:** Web Crawler Service (`app/service/web_crawler.py`)

## 1. Mô tả lỗi (Description)
Do website `ThuocBietDuoc.com.vn` và `TrungTamThuoc.com` thay đổi giao diện, bộ crawler không tìm thấy ô nhập liệu (Input field not found) hoặc không nhấn được nút tìm kiếm. Điều này dẫn đến việc không thu thập được dữ liệu bổ sung cho thuốc/bệnh.

## 2. Logs & Error Message (QUAN TRỌNG)
```text
Error during search on thuocbietduoc.com.vn: Input field not found for selector: 'input#search_keyword'
```

## 3. Cách khắc phục (Resolution)
- Cập nhật bộ Selectors linh hoạt hơn (hỗ trợ cả XPath và CSS).
- Thêm logic xử lý các trường hợp input ẩn hoặc nút tìm kiếm dạng icon.
- Tối ưu hóa thời gian chờ (`wait_until='networkidle'`).

## 4. Xác nhận (Verification)
Đã chạy `debug_search.py`, crawler hiện đã tìm được chính xác kết quả cho "Candesartan" và "Metformin".
