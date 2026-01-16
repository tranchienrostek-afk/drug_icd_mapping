# Deployment Guide - Medical API System

## Thông tin hệ thống
- **Version**: 1.0.0
- **API Base URL**: `/api/v1`
- **Swagger Docs**: `/docs`

---

## Yêu cầu hệ thống

### Server
- Docker Engine 20.x+
- Docker Compose 2.x+
- RAM: Tối thiểu 2GB
- Storage: 10GB+

### Network
- Port 8000 (hoặc cấu hình qua `HOST_PORT`)
- Outbound HTTPS (443) cho Azure OpenAI

---

## Cài đặt

### 1. Clone và chuẩn bị

```bash
cd /path/to/drug_icd_mapping/fastapi-medical-app
```

### 2. Cấu hình Environment

Copy file `.env.production` và điều chỉnh:

```bash
cp .env.production .env
```

**Quan trọng**: Thay đổi các API keys trước khi deploy production.

### 3. Build Docker Image

```bash
# Development (with hot reload)
docker-compose up -d --build

# Production (with workers)
docker build -t medical-api:prod -f Dockerfile.prod .
docker run -d -p 8000:8000 --env-file .env --name medical-api medical-api:prod
```

---

## API Endpoints

### Health Check
```
GET /api/v1/health
```

### Drug APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/drugs/identify` | POST | Xác định thông tin thuốc |
| `/api/v1/drugs/{id}` | GET | Lấy chi tiết thuốc |
| `/api/v1/drugs/search` | GET | Tìm kiếm thuốc |

### Disease APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/diseases/lookup` | POST | Tra cứu bệnh ICD |

### Consultation API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/consult_integrated` | POST | Tư vấn thuốc-bệnh (AI) |

### Analysis API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analysis/treatment-analysis` | POST | Phân tích phác đồ điều trị |

### Admin APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/drugs` | GET/POST/DELETE | Quản lý thuốc |
| `/api/v1/admin/diseases` | GET/POST/DELETE | Quản lý bệnh |
| `/api/v1/admin/links` | GET/DELETE | Quản lý Knowledge Base |

---

## Monitoring

### Logs
```bash
docker logs -f medical-api
```

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "ok",
  "services": {
    "drug_search": "available",
    "consultation": "available",
    "crawler": "available"
  }
}
```

---

## Troubleshooting

### Container không khởi động
1. Kiểm tra logs: `docker logs medical-api`
2. Kiểm tra file `.env` có đầy đủ biến môi trường
3. Kiểm tra database file exists: `app/database/medical.db`

### API trả về lỗi 500
1. Kiểm tra Azure OpenAI API key còn valid
2. Kiểm tra network có thể reach Azure endpoint

### Crawler không hoạt động
1. Container cần Chromium browser (đã có trong Dockerfile)
2. Một số websites có thể block IP - cần rotate proxy nếu cần

---

## Liên hệ hỗ trợ

Nếu có vấn đề, vui lòng liên hệ team phát triển.
