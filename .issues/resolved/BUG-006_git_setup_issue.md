# ISSUE: BUG-006 - Thiếu Git và lỗi cấu hình Path hệ thống
**Status:** Resolved
**Severity:** Medium
**Affected Component:** DevOps / Deployment

## 1. Mô tả lỗi (Description)
Hệ thống Windows không có sẵn lệnh `git`, dẫn đến việc không thể quản lý phiên bản hoặc đẩy code lên GitHub. Sau khi cài đặt qua `winget`, biến môi trường `Path` không được cập nhật ngay lập tức trong phiên làm việc hiện tại.

## 2. Logs & Error Message (QUAN TRỌNG)
```text
'git' is not recognized as an internal or external command, operable program or batch file.
```

## 3. Cách khắc phục (Resolution)
- Cài đặt Git sử dụng lệnh: `winget install --id Git.Git -e --source winget`.
- Truy cập trực tiếp qua đường dẫn tuyệt đối: `C:\Program Files\Git\cmd\git.exe` thay vì gọi lệnh `git` ngắn gọn.
- Thực hiện `git config` cho `user.name` và `user.email`.

## 4. Xác nhận (Verification)
Đã đẩy thành công mã nguồn lên GitHub tại repository `tranchienrostek-afk/drug_icd_mapping`.
