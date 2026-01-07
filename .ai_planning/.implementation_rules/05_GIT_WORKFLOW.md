# GIT WORKFLOW & STANDARDS

Tài liệu này quy chuẩn cách quản lý mã nguồn và làm việc với Git.

## 1. Branch Strategy
- **main:** Nhánh ổn định nhất, chỉ chứa code đã qua kiểm thử và sẵn sàng deploy.
- **develop:** Nhánh tích hợp các tính năng mới.
- **feature/<task-id>-<description>:** Nhánh làm việc cho từng tính năng cụ thể (ví dụ: `feature/003-optimize-crawler`).
- **bugfix/<issue-id>-<description>:** Nhánh sửa lỗi.

## 2. Commit Message Standards (Conventional Commits)
Sử dụng cấu trúc: `<type>(<scope>): <subject>`
- **feat:** Tính năng mới.
- **fix:** Sửa lỗi.
- **docs:** Thay đổi tài liệu.
- **refactor:** Tái cấu trúc code (không thay đổi tính năng).
- **test:** Thêm hoặc sửa test.
- **chore:** Các thay đổi phụ trợ cho hệ thống build, tool.

Ví dụ: `feat(api): add identification logic for drugs without SDK`

## 3. Pull Request (PR) Rules
- Mọi PR phải được kiểm tra (Code Review) trước khi merge.
- Phải đảm bảo mọi test case vượt qua thành công.
- Tuyệt đối không commit các file nhạy cảm (`.env`, database file, `__pycache__`).

## 4. .gitignore
- Luôn cập nhật `.gitignore` để tránh rác repository.
- Các tệp tin log (`*.log`) và dữ liệu nháp (`*.png`, `*.html` debugging) phải được loại bỏ.
