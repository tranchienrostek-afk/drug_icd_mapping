# Task 045: Deploy với Staging Pipeline

**Status**: 🚀 SẴN SÀNG  
**Date**: 2026-01-27  
**Strategy**: Staging → Test → Promote to Prod

---

## 📋 Files đã tạo

| File | Mô tả |
|------|-------|
| `docker-compose.staging.yml` | Staging container (port 8001) |
| `scripts/setup_staging.sh` | Setup staging lần đầu |
| `scripts/deploy_staging.sh` | Deploy + Test + Log |
| `scripts/promote_to_prod.sh` | Promote staging → prod |

---

## 🔄 Flow Deploy

```
Local: git push origin main
              ↓
Server: ./setup_staging.sh (lần đầu)
              ↓
Server: ./scripts/deploy_staging.sh
              ↓
        [Pull → Build → Unittest]
              ↓
        Log: staging/2026-01-27_XXXXXX_SUCCESS.log
              ↓
Server: ./scripts/promote_to_prod.sh
              ↓
        [Deploy Prod → Health Check]
              ↓
        Log: production/2026-01-27_XXXXXX_DEPLOYED.log
```

---

## 📝 HƯỚNG DẪN TỪNG BƯỚC

### BƯỚC 1: Check port 8001 (trên Server)

```bash
ss -tuln | grep 8001
```
Nếu không có output = OK

---

### BƯỚC 2: Commit & Push (Local - PowerShell)

```powershell
cd C:\Users\Admin\Desktop\drug_icd_mapping
git add .
git commit -m "feat: add staging pipeline with logging"
git push origin main
```

---

### BƯỚC 3: Setup Staging (Server - lần đầu)

```bash
# Tạo staging folder và clone repo
cd /root/workspace
git clone https://github.com/tranchienrostek-afk/drug_icd_mapping.git drug_icd_mapping_staging

# Vào folder và tạo thư mục logs
cd drug_icd_mapping_staging/fastapi-medical-app
mkdir -p /root/workspace/deploy_logs/staging
mkdir -p /root/workspace/deploy_logs/production

# Tạo .env
cat > .env << 'EOF'
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5434
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres@2024
POSTGRES_DB=medical_db
DB_TYPE=postgres

AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=<YOUR_AZURE_API_KEY>
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_DEPLOYMENT_NAME=gpt-4o-mini
OPENAI_API_KEY=<YOUR_AZURE_API_KEY>
OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-06-01
OPENAI_API_BASE=https://your-resource.cognitiveservices.azure.com/
OPENAI_BASE_URL=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_KEY=<YOUR_AZURE_API_KEY>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini
EOF

chmod +x scripts/*.sh
```

---

### BƯỚC 4: Deploy Staging

```bash
cd /root/workspace/drug_icd_mapping_staging/fastapi-medical-app
./scripts/deploy_staging.sh
```

**Output mong đợi:**
- Container build thành công
- Unittest chạy và PASS
- Log file: `/root/workspace/deploy_logs/staging/2026-01-27_XXXXXX_SUCCESS.log`

---

### BƯỚC 5: Verify Staging

```bash
# Health check
curl http://localhost:8001/api/v1/health

# Test search
curl "http://localhost:8001/api/v1/drugs/search?q=paracetamol"

# Xem logs
ls -la /root/workspace/deploy_logs/staging/
```

---

### BƯỚC 6: Promote to Production

```bash
cd /root/workspace/drug_icd_mapping/fastapi-medical-app
chmod +x scripts/*.sh
./scripts/promote_to_prod.sh
```

---

## 📂 Cấu trúc Logs

```
/root/workspace/deploy_logs/
├── staging/
│   ├── 2026-01-27_100000_SUCCESS.log
│   ├── 2026-01-27_110000_FAILED.log
│   └── .last_success_commit
└── production/
    ├── 2026-01-27_120000_DEPLOYED.log
    └── .last_prod_commit (for rollback)
```

---

## 🚨 Rollback Production

```bash
cd /root/workspace/drug_icd_mapping/fastapi-medical-app
LAST_COMMIT=$(cat /root/workspace/deploy_logs/production/.last_prod_commit)
git reset --hard $LAST_COMMIT
docker-compose up -d --build
```

---

## ✅ Checklist

### Trước khi bắt đầu:
- [ ] Check port 8001: `ss -tuln | grep 8001`
- [ ] Database `medical_db` đã tạo ✅

### Deploy process:
- [ ] Commit & Push code từ local
- [ ] Setup staging (lần đầu)
- [ ] Run `deploy_staging.sh`
- [ ] Verify staging hoạt động
- [ ] Run `promote_to_prod.sh`
- [ ] Verify production hoạt động
