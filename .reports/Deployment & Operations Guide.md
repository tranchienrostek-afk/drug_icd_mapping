# 🏥 Drug ICD Mapping - Deployment & Operations Guide

> **Phiên bản:** 3.0 | **Cập nhật:** 2026-01-27 | **Author:** AI Development Team

---

## 🌊 Push to Git, Everything Flows

> **Triết lý:** Developer chỉ cần `git push origin main` - mọi thứ còn lại sẽ tự động chạy như dòng suối.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        🌊 AUTOMATIC CI/CD FLOW                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   git push     GitHub      Staging        Tests        Production            │
│   ───────►    Actions ───► Deploy ────► ✅ Pass ────►  Deploy                │
│                  │           :8001                       :8000                │
│                  │             │                                             │
│                  │             ▼ ❌ Fail                                      │
│                  │         ┌────────┐                                        │
│                  └────────►│  STOP  │  (Không promote)                       │
│                            └────────┘                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Quy trình tự động

| Step | Tự động | Thời gian | Mô tả |
|------|---------|-----------|-------|
| 1 | ✅ | 0-1 phút | GitHub Actions trigger khi push `main` |
| 2 | ✅ | 2-5 phút | Deploy Staging (rebuild Docker image) |
| 3 | ✅ | 1-2 phút | Chạy Health Check + Unit Tests |
| 4 | ✅ | 2-5 phút | **Nếu tests pass** → Deploy Production |
| 5 | ✅ | 0-1 phút | Production Health Check |

**Tổng thời gian: ~10 phút từ push đến production!**

---

## 📌 Tổng quan dự án

### Mục đích
Hệ thống mapping thuốc với mã ICD, hỗ trợ bác sĩ tra cứu và tư vấn kê đơn thông minh.

### Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| **Backend** | FastAPI (Python 3.10+) |
| **Database** | PostgreSQL 16 (production), SQLite (dev) |
| **AI/LLM** | Azure OpenAI (GPT-4o-mini) |
| **Container** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions (Self-hosted Runner) |
| **Monitoring** | Built-in Dashboard `/monitor` |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
               ┌───────────▼───────────┐
               │  Nginx Proxy Manager  │  :80/:443
               │  (Reverse Proxy)      │
               └───────────┬───────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │  PROD   │       │ STAGING │       │ MONITOR │
    │  :8000  │       │  :8001  │       │ /monitor│
    └────┬────┘       └────┬────┘       └─────────┘
         │                 │
         │    ┌────────────┼────────────────┐
         │    │            │                │
    ┌────▼────▼────┐  ┌────▼────┐     ┌─────▼─────┐
    │  PostgreSQL  │  │  Redis  │     │  Qdrant   │
    │    :5434     │  │  :6379  │     │   :6333   │
    └──────────────┘  └─────────┘     └───────────┘
```

---

## 🖥️ Server Information

| Thông tin | Giá trị |
|-----------|---------|
| **IP** | `10.14.190.28` |
| **SSH** | `ssh root@10.14.190.28` |
| **OS** | Ubuntu 22.04 |
| **RAM** | 128GB |
| **Disk** | ~500GB |

### URLs quan trọng

| URL | Mô tả |
|-----|-------|
| `http://10.14.190.28:8000` | Production API |
| `http://10.14.190.28:8001` | Staging API |
| `http://10.14.190.28:8000/docs` | Swagger UI |
| `http://10.14.190.28:8000/monitor` | 📊 **Dashboard Monitor** |

### Thư mục quan trọng

```bash
/root/workspace/
├── drug_icd_mapping/              # PRODUCTION
│   └── fastapi-medical-app/       # App folder
├── drug_icd_mapping_staging/      # STAGING  
│   └── fastapi-medical-app/
├── deploy_logs/                   # Deployment logs
└── db_backup/                     # Database backups
```

---

## 🚀 Developer Workflow

### Cách duy nhất để deploy: Push to Git!

```bash
# 1. Làm việc trên local
git add .
git commit -m "feat: new feature"

# 2. Push và chờ 🌊
git push origin main

# 3. Theo dõi trên GitHub Actions
# https://github.com/<org>/<repo>/actions
```

> [!TIP]
> **Không cần SSH vào server!** GitHub Actions sẽ tự động deploy.

### Theo dõi CI/CD Pipeline

1. Mở GitHub Repository → **Actions** tab
2. Click vào workflow run mới nhất
3. Xem logs từng stage: Staging → Tests → Production

### Trigger paths

CI/CD **chỉ chạy** khi thay đổi files trong:
- `fastapi-medical-app/**` (code)
- `.github/workflows/**` (CI/CD config)

---

## 🔐 Cấu hình môi trường

### File `.env` (Template)

```env
# Database - PostgreSQL (External Container)
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5434
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<YOUR_PASSWORD>
POSTGRES_DB=medical_db
DB_TYPE=postgres

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=<YOUR_API_KEY>
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_KEY=<YOUR_API_KEY>
```

> [!CAUTION]
> **File `.env` KHÔNG được commit lên Git!**
> 
> `.env` đã được cấu hình sẵn trên server. Chỉ sửa khi thay đổi API keys.

---

## 📊 Monitoring Dashboard

Truy cập: **http://10.14.190.28:8000/monitor**

### Features

| Tab | Nội dung |
|-----|----------|
| **Summary** | Request counts, API stats |
| **System** | CPU/RAM/Disk gauges, Network I/O, Uptime |
| **Request Detail** | Chi tiết từng request, response JSON |

### API Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health

# System stats
curl http://localhost:8000/api/v1/monitor/stats

# Detailed hardware info
curl http://localhost:8000/api/v1/monitor/system
```

---

## 🐳 Docker Commands (Chỉ khi cần)

> [!NOTE]
> Thông thường KHÔNG cần chạy các lệnh này vì CI/CD tự động xử lý.

### Xem containers

```bash
docker ps | grep drug                   # Running containers
docker logs drug_icd_mapping_prod_web --tail=100
```

### Restart thủ công (khẩn cấp)

```bash
# Chỉ restart (không rebuild)
docker restart drug_icd_mapping_prod_web

# Rebuild hoàn toàn (khi .env thay đổi)
cd /root/workspace/drug_icd_mapping/fastapi-medical-app
docker-compose rm -f -s web && docker-compose up -d web
```

---

## 🗄️ Database

### Thông tin kết nối

| Param | Value |
|-------|-------|
| Host | `host.docker.internal` (trong container) |
| Port | `5434` |
| User | `postgres` |
| Database | `medical_db` |

### Truy cập PostgreSQL

```bash
docker exec -it postgres-db psql -U postgres -d medical_db

# Useful commands
\dt                     # List tables
SELECT count(*) FROM drugs;
SELECT count(*) FROM knowledge_base;
```

### Backup Database

```bash
# Backup
docker exec postgres-db pg_dump -U postgres medical_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i postgres-db psql -U postgres medical_db < backup_file.sql
```

---

## 🧪 Testing

### Unit tests chạy tự động trong CI/CD!

Nếu cần chạy thủ công:

```bash
docker exec -it drug_icd_staging_web pytest /app/unittest/ -v --tb=short
```

---

## 🔧 Troubleshooting

### CI/CD Pipeline Failed

1. **Xem logs trên GitHub Actions**
2. Kiểm tra stage nào fail:
   - Staging deploy fail → Docker build error
   - Tests fail → Code bug
   - Production fail → Server issue

### Container không start

```bash
# Xem logs
docker logs drug_icd_mapping_prod_web --tail=100

# Kiểm tra .env
docker exec -it drug_icd_mapping_prod_web env | grep -i postgres
docker exec -it drug_icd_mapping_prod_web env | grep -i azure
```

### Database connection error

```bash
# Test connection
docker exec -it postgres-db psql -U postgres -d medical_db -c "SELECT 1;"
```

### Known Issues & Workarounds

| Issue | Giải pháp |
|-------|-----------|
| `ContainerConfig KeyError` | Bug docker-compose 1.29.2: `docker-compose rm -f -s web && docker-compose up -d web` |
| `.env` không apply | Container cần recreate: `docker-compose rm -f -s web && docker-compose up -d web` |
| SSH disconnect lúc build | CI/CD tự xử lý, không cần SSH |
| Git clone chậm | CI/CD dùng `git fetch + reset --hard` |

---

## 📝 Commit Convention

```
feat: add new feature
fix: bug fix
docs: documentation
refactor: code refactoring
test: add tests
chore: maintenance
```

---

## 📞 Support

| Role | Contact |
|------|---------|
| DevOps | (Self-hosted Runner on Server) |
| Backend | Trần Chiến |

### Logs Location
- CI/CD Logs: GitHub Actions → Workflow runs
- Docker Logs: `docker logs <container_name>`
- App Monitor: `/monitor` dashboard

---

## 📈 Data Stats (2026-01-27)

| Table | Records |
|-------|---------|
| drugs | 83,770 |
| diseases | 15,832 |
| knowledge_base | 17,978 |

---

*🌊 Push to Git, Everything Flows! - Automated by GitHub Actions CI/CD*
