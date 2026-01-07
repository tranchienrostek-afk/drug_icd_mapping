# ISSUE: [BUG-ID] - [TÊN LỖI NGẮN GỌN]
**Status:** Open
**Severity:** High/Medium/Low
**Affected Component:** (Ví dụ: Crawler Service, Database API)

## 1. Mô tả lỗi (Description)
*Mô tả ngắn gọn điều gì đang xảy ra sai.*
> Ví dụ: Khi submit thuốc trùng SĐK, hệ thống không chuyển sang Staging mà báo lỗi 500 Internal Server Error.

## 2. Logs & Error Message (QUAN TRỌNG)
*Copy paste nguyên văn log lỗi vào đây. AI cần cái này nhất.*
```text
Traceback (most recent call last):
  File "services.py", line 45, in create_drug
    return db.add(new_drug)
IntegrityError: duplicate key value violates unique constraint "drugs_sdk_key"