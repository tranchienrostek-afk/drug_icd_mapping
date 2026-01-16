# Production Readiness Implementation Plan

## Mục tiêu
Hoàn thiện dự án `fastapi-medical-app` để bàn giao cho khách hàng. Dự án bao gồm các API tra cứu thuốc, bệnh (ICD), và tư vấn dược lý sử dụng AI.

## Tình trạng hiện tại

### ✅ Đã hoàn thiện
| Thành phần | File | Trạng thái |
|------------|------|------------|
| Drug Search Service | `app/service/drug_search_service.py` | ✅ Đầy đủ (Exact, Fuzzy, TF-IDF) |
| Drug Approval Service | `app/service/drug_approval_service.py` | ✅ Đầy đủ (Staging, Approve, Reject) |
| Consultation Service | `app/service/consultation_service.py` | ✅ Đầy đủ (KB + AI Fallback) |
| AI Consult Service | `app/service/ai_consult_service.py` | ✅ Đầy đủ (Azure OpenAI) |
| Web Crawler | `app/service/crawler/` | ✅ Đầy đủ (Multi-site, Anti-bot) |
| Database Core | `app/database/core.py` | ✅ Đầy đủ (Migration, FTS) |
| Drug Repository | `app/service/drug_repo.py` | ✅ Đầy đủ |
| Normalizers | `app/core/utils.py` | ✅ Đầy đủ |
| Classification | `app/core/classification.py` | ✅ Đầy đủ |
| Middleware | `app/core/middleware.py` | ✅ Đầy đủ (Logging) |

### ⚠️ Cần hoàn thiện (Stubs)
| Thành phần | File | Vấn đề |
|------------|------|--------|
| DiseaseDbEngine | `app/services.py` | Chỉ là stub, cần tạo `app/service/disease_service.py` |
| delete_drug/delete_disease | `app/services.py` | Stub, cần implement trong Repository |
| check_knowledge_base | `app/services.py` | Stub, cần kết nối đến bảng `knowledge_base` |
| log_raw_data | `app/services.py` | Stub, cần lưu vào bảng `raw_logs` |
| process_raw_log | `app/service/etl_service.py` | Stub, cần implement ETL logic |

---

## Proposed Changes

### 1. [New] `app/service/disease_service.py`
Tạo service xử lý bệnh ICD tương tự DrugSearchService:
- `search(name, icd10)`: Tra cứu bảng `diseases` hoặc `knowledge_base`
- `get_diseases_list()`: Phân trang danh sách
- `save_disease()`, `delete_disease()`: CRUD operations

### 2. [Modify] `app/service/drug_repo.py`
Thêm các phương thức xóa:
- `delete_drug(sdk)`: Xóa theo Số Đăng Ký
- `delete_drug_by_id(row_id)`: Xóa theo ID

### 3. [Modify] `app/services.py` (Facade)
- Delegate `delete_drug`, `delete_drug_by_id` đến `DrugRepository`
- Delegate `DiseaseDbEngine` đến `DiseaseService`
- Implement `check_knowledge_base(sdks, icds)` thực sự truy vấn DB

### 4. [Modify] `app/service/etl_service.py`
Implement `process_raw_log`:
- Parse CSV content
- Clean/Validate records
- Insert vào `knowledge_base` table

### 5. [New] `app/main.py` - Health Check Endpoint
Thêm endpoint `/api/v1/health` cho monitoring.

### 6. [Modify] `requirements.txt`
Thêm phiên bản cố định để đảm bảo tương thích.

### 7. [New] Production Security
- Xóa API keys khỏi `.env.production` (chuyển sang biến môi trường Docker/Cloud)
- Thêm CORS cấu hình chuẩn

---

## Verification Plan

### Automated Tests (Docker)
1. Build image: `docker build -t medical-api:prod -f Dockerfile.prod .`
2. Run container: `docker run -p 8000:8000 --env-file .env.production medical-api:prod`
3. Test endpoints:
   - `GET /api/v1/health` → 200 OK
   - `POST /api/v1/drugs/identify` với sample data
   - `POST /api/v1/consult_integrated` với sample data

### Manual Verification
- Swagger UI: `http://localhost:8000/docs`
- Kiểm tra logs trong Docker: `docker logs <container>`
