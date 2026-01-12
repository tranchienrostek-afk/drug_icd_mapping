# Task 024: Deploy System to Dev Server

**Trạng thái:** Active
**Priority:** High
**Assignee:** DevOps Engineer
**Created Date:** 2026-01-09

## 1. Context (Bối cảnh)
Hệ thống hiện tại chạy tốt trên Local (Windows/Docker). Cần triển khai lên Server Dev nội bộ để đội ngũ Test/BA có thể truy cập và kiểm thử trên môi trường gần với Production.

## 2. Server Information
- **IP:** `10.14.190.28`
- **User:** `root`
- **Password:** `Ua>7@[*FK]1$o6chd9`
- **OS:** Linux (Cần verify phiên bản cụ thể: Ubuntu/CentOS?)

## 3. Implementation Plan

### Step 1: Server Preparation
- [ ] SSH vào server kiểm tra môi trường.
- [ ] Cài đặt Docker & Docker Compose (nếu chưa có).
- [ ] Tạo thư mục dự án `/opt/drug_icd_mapping` (hoặc tương tự).

### Step 2: Deployment
- [ ] Transfer source code từ Local -> Server (SC, Rsync hoặc Git Clone).
  - *Lưu ý:* Nếu dùng Git, cần đảm bảo `medical.db` và các file `datacore` lớn được xử lý đúng (Git LFS hoặc copy thủ công `scp`).
- [ ] Build Docker Image trên Server (`docker-compose up -d --build`).

### Step 3: Configuration
- [ ] Setup Environment Variables (`.env`).
- [ ] Open Firewall/Ports (Map port 8000 -> 80 hoặc giữ nguyên 8000).

### Step 4: Verification
- [ ] Kiểm tra API Healthcheck (`/docs`).
- [ ] Run benchmark test trên server để so sánh hiệu năng (Xem RAM/CPU usage).

## 4. Acceptance Criteria
- [ ] Hệ thống chạy ổn định trên IP `10.14.190.28:8000` (hoặc port chỉ định).
- [ ] Các tính năng Search (Exact, Fuzzy, Vector) hoạt động chính xác.
- [ ] Dữ liệu 65k thuốc khả dụng trên server.
