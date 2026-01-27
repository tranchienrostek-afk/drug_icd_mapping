# 🏥 Drug ICD Mapping - Deployment & Operations Guide

> **Phiên bản:** 2.0 | **Cập nhật:** 2026-01-27 | **Author:** AI Development Team

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
| **Reverse Proxy** | Nginx Proxy Manager |
| **Monitoring** | SignOz |

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
    │  PROD   │       │ STAGING │       │  OTHER  │
    │  :8000  │       │  :8001  │       │ SERVICES│
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

### Thư mục quan trọng

```bash
/root/workspace/
├── drug_icd_mapping/              # PRODUCTION
│   └── fastapi-medical-app/       # App folder
├── drug_icd_mapping_staging/      # STAGING
│   └── fastapi-medical-app/
├── deploy_logs/                   # Deployment logs
│   ├── staging/                   # Staging logs
│   └── production/                # Production logs
└── db_backup/                     # Database backups
```

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
```

> ⚠️ **QUAN TRỌNG:** File `.env` KHÔNG được commit lên Git!

---

## 🚀 Quy trình Deploy

### Sơ đồ Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  LOCAL   │───►│  GITHUB  │───►│ STAGING  │───►│   PROD   │
│  Dev     │push│   Main   │pull│  :8001   │test│  :8000   │
└──────────┘    └──────────┘    └──────────┘pass└──────────┘
                                     │
                                     ▼ fail
                              ┌──────────┐
                              │   FIX    │
                              │  BUGS    │
                              └──────────┘
```

### Bước 1: Deploy Staging

```bash
cd /root/workspace/drug_icd_mapping_staging/fastapi-medical-app
./scripts/deploy_staging.sh
```

**Script này sẽ:**
1. Pull code mới từ GitHub
2. Build Docker image
3. Chạy container trên port 8001
4. Chạy unittest
5. Log kết quả (SUCCESS/FAILED)

### Bước 2: Verify Staging

```bash
# Health check
curl http://localhost:8001/api/v1/health

# Test API
curl http://localhost:8001/docs
```

### Bước 3: Promote to Production

> [!CAUTION]
> **KIỂM TRA DATA TRƯỚC KHI PROMOTE!**
> 
> Đảm bảo database PostgreSQL đã có đầy đủ data từ SQLite:
> ```bash
> # Kiểm tra số records
> docker exec -it postgres-db psql -U postgres -d medical_db -c "SELECT count(*) FROM drugs;"
> docker exec -it postgres-db psql -U postgres -d medical_db -c "SELECT count(*) FROM knowledge_base;"
> 
> # Nếu số lượng ít (< 100), cần chạy migration:
> cd /root/workspace/drug_icd_mapping_staging/fastapi-medical-app
> docker exec -it drug_icd_staging_web python scripts/migrate_data_to_postgres.py
> ```

**Bước 3.1: Pull code mới vào prod folder**

```bash
cd /root/workspace/drug_icd_mapping
git pull origin main
cd fastapi-medical-app
chmod +x scripts/*.sh
```

**Bước 3.2: Chạy promote script**

```bash
./scripts/promote_to_prod.sh
```

**Bước 3.3: Kiểm tra sau promote**

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Xem container
docker ps | grep drug_icd_mapping_prod

# Xem logs
docker logs drug_icd_mapping_prod_web_1 --tail=50
```

> [!WARNING]  
> **Nếu lần đầu deploy hoặc thay đổi requirements.txt:**
> - Docker sẽ rebuild image (~10-20 phút tùy mạng)
> - Dùng `screen` hoặc `nohup` để tránh SSH disconnect
> ```bash
> screen -S prod_deploy
> ./scripts/promote_to_prod.sh
> # Nhấn Ctrl+A, D để detach
> # Quay lại: screen -r prod_deploy
> ```

---

## 📁 Scripts quan trọng

| Script | Mục đích |
|--------|----------|
| `scripts/deploy_staging.sh` | Deploy staging + unittest |
| `scripts/promote_to_prod.sh` | Promote staging → prod |
| `scripts/setup_staging.sh` | Setup staging lần đầu |
| `deploy_prod.sh` | Deploy prod trực tiếp |

---

## 🐳 Docker Commands

### Xem containers
```bash
docker ps                                    # Running containers
docker ps -a                                 # All containers
docker ps | grep drug                        # Filter drug containers
```

### Xem logs
```bash
docker logs drug_icd_mapping_prod_web_1 --tail=100
docker logs drug_icd_staging_web --tail=100 -f
```

### Restart container
```bash
docker restart drug_icd_mapping_prod_web_1
docker restart drug_icd_staging_web
```

### Vào container
```bash
docker exec -it drug_icd_staging_web bash
docker exec -it drug_icd_mapping_prod_web_1 bash
```

### Build & Deploy thủ công
```bash
# Staging
docker-compose -f docker-compose.staging.yml up -d --build

# Production
docker-compose up -d --build
```

---

## 🗄️ Database

### Thông tin kết nối

| Param | Value |
|-------|-------|
| Host | `host.docker.internal` (trong container) |
| Host | `localhost` (trên server) |
| Port | `5434` |
| User | `postgres` |
| Database | `medical_db` |

### Truy cập PostgreSQL

```bash
# Từ server
docker exec -it postgres-db psql -U postgres -d medical_db

# Một số lệnh hữu ích
\dt                     # List tables
\d+ drugs               # Describe table
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

### Chạy unittest trong container

```bash
docker exec -it drug_icd_staging_web pytest unittest/ -v --tb=short
```

### Chạy test cụ thể

```bash
# Chạy 1 file test
docker exec -it drug_icd_staging_web pytest unittest/test_comprehensive_api.py -v

# Chạy 1 test function
docker exec -it drug_icd_staging_web pytest unittest/test_comprehensive_api.py::TestDrugsAPI::test_search_drugs -v
```

---

## ⚡ Fast Staging Testing (Không rebuild Docker)

> **QUAN TRỌNG:** Khi fix bug và cần test nhanh, KHÔNG chạy `deploy_staging.sh` vì sẽ rebuild Docker (~20 phút). Thay vào đó dùng các cách sau:

### Cách 1: Pull code + Restart (Không đổi requirements)

```bash
cd /root/workspace/drug_icd_mapping_staging/fastapi-medical-app

# Pull code mới
git pull origin main

# Chỉ restart container (không rebuild)
docker restart drug_icd_staging_web

# Chạy test
docker exec -it drug_icd_staging_web pytest unittest/ -v --tb=short
```

### Cách 2: Thêm package mới vào container đang chạy

```bash
# Cài package trực tiếp vào container (tạm thời)
docker exec -it drug_icd_staging_web pip install <package-name>

# Chạy test
docker exec -it drug_icd_staging_web pytest unittest/ -v --tb=short
```

### Cách 3: Mount code trực tiếp (Dev mode)

```bash
# Tạo container với volume mount (code thay đổi tự động cập nhật)
docker run -d --name staging_dev \
  -v $(pwd):/app \
  -p 8002:8000 \
  --env-file .env \
  fastapi-medical-app_staging-web \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Khi nào cần rebuild?

| Thay đổi | Rebuild? | Lệnh |
|----------|----------|------|
| Chỉ sửa code Python | ❌ Không | `docker restart` |
| Thêm package requirements | ⚠️ Có thể dùng `pip install` tạm | `docker exec ... pip install` |
| Đổi Dockerfile | ✅ Có | `deploy_staging.sh` |
| Đổi base image | ✅ Có | `deploy_staging.sh` |

---

## 🔧 Troubleshooting

### Container không start

```bash
# Xem logs
docker logs drug_icd_staging_web --tail=100

# Kiểm tra port đang dùng
ss -tuln | grep 8001

# Restart
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d
```

### Database connection error

```bash
# Kiểm tra postgres container
docker ps | grep postgres

# Test connection từ trong container
docker exec -it drug_icd_staging_web python -c "
from app.database.core import DatabaseCore
db = DatabaseCore()
conn = db.get_connection()
print('Connection OK:', conn)
"
```

### Permission denied khi chạy script

```bash
chmod +x scripts/*.sh
./scripts/deploy_staging.sh
```

---

## 📊 Monitoring

### Health Check Endpoints

| Endpoint | Mục đích |
|----------|----------|
| `/api/v1/health` | App health |
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |

### Kiểm tra resources

```bash
# Disk usage
df -h

# Memory
free -h

# Docker disk usage
docker system df
```

### Dọn dẹp Docker

```bash
# Xóa images không dùng
docker image prune -a

# Xóa tất cả không dùng
docker system prune -a
```

---

## 📝 Lessons Learned

### ✅ Best Practices

1. **Luôn test trên staging trước** - Không deploy thẳng prod
2. **Backup database trước khi migrate** - pg_dump trước mọi thay đổi
3. **Kiểm tra requirements.txt** - Đảm bảo dependencies đầy đủ
4. **Không commit secrets** - Dùng .env và .gitignore

### ⚠️ Known Issues

| Issue | Giải pháp |
|-------|-----------|
| SSH disconnect lúc build | Dùng `screen` hoặc `nohup` |
| Git clone chậm | Copy từ prod + git fetch |
| PostgreSQL cursor type | Check `isinstance(res, dict)` |
| Async test fail | Thêm `pytest-asyncio` |
| Mocker fixture not found | Thêm `pytest-mock` |
| datetime serialization | Dùng `field_serializer` trong Pydantic |
| Port already allocated | Stop container cũ trước: `docker stop <name>` |
| ContainerConfig KeyError | Bug docker-compose 1.29.2: Dùng `docker-compose rm -f -s web && docker-compose up -d web` |
| DrugMatcher db_path error | Sửa `DrugMatcher(db_path=db_path)` → `DrugMatcher()` |
| Restart không update code | Code trong image, restart chỉ restart container. Cần rebuild hoặc patch |

---

## 🔑 API Keys & Environment

> [!CAUTION]
> **Container KHÔNG tự đọc lại .env khi restart!**

### Vấn đề: Thay đổi .env nhưng container không nhận

```bash
# ❌ SAI - Restart không đủ
docker restart drug_icd_mapping_prod_web

# ✅ ĐÚNG - Phải recreate container
docker-compose rm -f -s web
docker-compose up -d web
```

### Quick Fix (Patch code trong container)

Khi cần sửa code gấp mà không muốn rebuild (~20 phút):

```bash
# Patch trực tiếp
docker exec -it <container_name> sed -i 's/old_code/new_code/' /app/path/to/file.py

# Restart để reload
docker restart <container_name>
```

> **Lưu ý:** Quick fix sẽ mất khi rebuild. Đảm bảo code đã push GitHub để rebuild sau có fix vĩnh viễn.

---

## 🩸 Kinh nghiệm xương máu - Data Migration

### Vấn đề: UUID trong cột INTEGER

Khi migrate từ SQLite → PostgreSQL, cột `disease_ref_id` và `secondary_disease_ref_id` có cả **INTEGER** và **UUID** → PostgreSQL reject.

**Triệu chứng:**
```
invalid input syntax for type integer: "adeca53e-5b2f-4fb9-87cf-df084288b5ff"
```

**Giải pháp:**
```bash
# Alter PostgreSQL schema sang TEXT
docker exec -it postgres-db psql -U postgres -d medical_db -c "
ALTER TABLE knowledge_base 
  ALTER COLUMN disease_ref_id TYPE TEXT,
  ALTER COLUMN secondary_disease_ref_id TYPE TEXT;
"

# Sau đó chạy lại migration
docker exec -it drug_icd_staging_web python scripts/migrate_data_to_postgres.py
```

### Checklist Migration

> [!IMPORTANT]
> **LUÔN kiểm tra data SAU khi migrate!**

```bash
# So sánh record count
# SQLite
docker exec -it drug_icd_staging_web python -c "
import sqlite3
conn = sqlite3.connect('/app/app/database/medical.db')
cursor = conn.cursor()
for table in ['drugs', 'diseases', 'knowledge_base']:
    cursor.execute(f'SELECT count(*) FROM {table}')
    print(f'{table}: {cursor.fetchone()[0]}')
"

# PostgreSQL
docker exec -it postgres-db psql -U postgres -d medical_db -c "
SELECT 'drugs', count(*) FROM drugs
UNION ALL SELECT 'diseases', count(*) FROM diseases
UNION ALL SELECT 'knowledge_base', count(*) FROM knowledge_base;
"
```

### Data đã migrate thành công (2026-01-27)

| Table | Records |
|-------|---------|
| drugs | 83,770 |
| diseases | 15,832 |
| knowledge_base | 17,978 |

---

## 🔄 Git Workflow

### Commit Convention

```
feat: add new feature
fix: bug fix
docs: documentation
refactor: code refactoring
test: add tests
chore: maintenance
```

### Push to GitHub

```bash
git add .
git commit -m "feat: description"
git push origin main
```

> ⚠️ **Lưu ý:** Auto-deploy đã tắt. Push không tự động deploy prod.

---

## 📞 Support

### Contacts
- **DevOps**: Chưa có
- **Backend**: Trần Chiến

### Logs Location
- Staging: `/root/workspace/deploy_logs/staging/`
- Production: `/root/workspace/deploy_logs/production/`

---

*Tài liệu này được cập nhật tự động bởi AI Assistant.*
