# Task 024: Deploy System to Dev Server

**Trạng thái:** Active
**Priority:** High
**Assignee:** DevOps Engineer
**Created Date:** 2026-01-09
**Updated Date:** 2026-01-14

## 1. Context (Bối cảnh)
Hệ thống Backend (FastAPI + SQLite + Agentic Services) đã hoàn thiện các tính năng core như Identify, Consult, và Knowledge Base ETL. Cần triển khai lên Server Dev nội bộ để đội ngũ Test/BA kiểm thử tích hợp (Integration Test) và đánh giá hiệu năng thực tế.

## 2. Server Information
- **IP:** `10.14.190.28`
- **User:** `root`
- **Password:** `Ua>7@[*FK]1$o6chd9`
- **OS:** Linux (Target: Ubuntu/CentOS)
- **Port Mapping:** 
  - Host: `Dynamic` (Cần check port trống, vd: 8005, 8006, 8010...)
  - Container: `8000`

## 3. Deployment Plan

### Phase 1: Preparation (Local)
1.  **Finalize Dockerfile**:
    - Ensure `fastapi-medical-app/Dockerfile` is optimized (Python 3.10-slim).
    - Include necessary system dependencies (gcc, curl for healthchecks).
2.  **Prepare Data Artifacts**:
    - `medical.db`: Database chính chứa Master Data (Thuốc, ICD) và Knowledge Base đã init.
    - `knowledge for agent/logs_to_database/logs.csv`: File logs gốc để test lại ETL flow trên server.
3.  **Environment Config**:
    - Tạo file `.env.production` mẫu với các key Azure OpenAI, Gemini (nếu dùng).

### Phase 2: Server Setup (Remote)
1.  **SSH Connection**:
    - `ssh root@10.14.190.28`
2.  **Check Available Ports**:
    - Server có nhiều service đang chạy, cần tìm port chưa sử dụng.
    - Run: `netstat -tulpn | grep :800` để xem các port 800x đã bị chiếm chưa.
    - Chọn một port trống, ví dụ `HOST_PORT=8006`.
3.  **Install Dependencies**:
    - Docker Engine latest.
    - Docker Compose plugin.
4.  **Directory Structure**:
    ```bash
    mkdir -p /root/workspace/drug_icd_mapping/data
    mkdir -p /root/workspace/drug_icd_mapping/logs
    ```

### Phase 3: Deployment Execution
1.  **Transfer Source Code**:
    - Option A (Git): Clone repository.
    - Option B (Manual): `scp -r ./fastapi-medical-app root@10.14.190.28:/root/workspace/drug_icd_mapping/`
2.  **Transfer Data**:
    - `scp ./medical.db root@10.14.190.28:/root/workspace/drug_icd_mapping/data/`
3.  **Configure & Deploy (SAFE MODE)**:
    - **Quan trọng**: Server có nhiều service khác. TUYỆT ĐỐI KHÔNG chạy lệnh `docker-compose down` hoặc `docker system prune -a` bừa bãi.
    - Đặt tên project cụ thể để tránh conflict:
      ```bash
      export COMPOSE_PROJECT_NAME=drug_icd_mapping
      ```
    - Chỉnh sửa `docker-compose.yml`: Đảm bảo service name là unique (vd: `app_medical_intel` thay vì `app`).
    - Build & Up **chỉ service của mình**:
      ```bash
      # Chỉ up service cụ thể, không đụng service khác
      HOST_PORT=8006 docker-compose up -d --build --no-deps app_medical_intel
      ```
    - Verify ps: `docker-compose ps` (Chỉ thấy container của mình).

### Phase 4: Verification & Smoke Test
1.  **Health Check**:
    - `curl http://10.14.190.28:<CHOSEN_PORT>/api/v1/health` -> Expect `200 OK`.
2.  **Functional Test**:
    - Ingest Test: Upload `logs.csv` qua API `/api/v1/data/ingest`.
    - Consult Test: Gọi API `/api/v1/consult` với payload mẫu `{"drug_name": "Panadol", "disease_name": "Đau đầu"}`.
3.  **Performance Monitor**:
    - Check RAM/CPU usage của container (`docker stats`).

## 4. Acceptance Criteria
- [ ] Container trạng thái `Up` (không restart loop).
- [ ] PORT Mapping chính xác không bị conflict (Service start thành công).
- [ ] API truy cập được từ mạng nội bộ qua IP `10.14.190.28:<CHOSEN_PORT>`.
- [ ] Database persist ok (dữ liệu không mất khi restart container).
- [ ] Knowledge Base hoạt động: Ingest CSV và Consult trả về kết quả đúng logic "Vote & Promote".
