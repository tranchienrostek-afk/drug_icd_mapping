# HANDOVER REPORT - DRUG ICD MAPPING PROJECT
**Date:** 2026-01-20
**Prepared By:** Antigravity AI Agent

## 1. Project Overview
This project implements a **Medical Consultation System** that checks drug-disease compatibility using:
1.  **Internal Knowledge Base (KB)**: SQLite database populated from trustworthy sources (TDV feedback).
2.  **External AI**: Fallback logic (currently disabled for safety in production) or used for ingestion suggestions.

**Current Status:** [PRODUCTION READY] on Development Server (10.14.190.28).

## 2. Architecture
- **Framework**: FastAPI (Python 3.10+).
- **Database**: SQLite (`app/database/medical.db`).
- **Deployment**: Docker Compose via GitHub Actions (Self-Hosted Runner).
- **Authentication**: None (Internal Service) / Rate Limiting (Ingest API).

## 3. Key Directories & Files
| Path | Description |
| :--- | :--- |
| `fastapi-medical-app/app/` | Main application source code. |
| `fastapi-medical-app/app/models.py` | Data models (Pydantic). **Check here for API Schemas.** |
| `fastapi-medical-app/app/service/consultation_service.py` | Core logic for Drug-ICD interaction checks. |
| `.github/workflows/deploy.yml` | CI/CD Pipeline configuration. |
| `scripts/` | Ops scripts (`upload_db.py`, `check_status.py`). |
| `knowledge for agent/` | Raw logs and data sources. |

## 4. Operational Procedures

### A. Deployment (How to update code)
The system uses **Automated CI/CD**.
1.  Make code changes locally.
2.  Commit and Push to `main`:
    ```bash
    git add .
    git commit -m "feat: description"
    git push origin main
    ```
3.  **Wait ~2-3 minutes**. The server will automatically:
    - Pull code.
    - Rebuild Docker images (if requirements changed).
    - Restart containers safely (with port cleanup).

### B. Ingesting Data (How to update DB)
Use the Injest API to upload CSV files.
- **Endpoint**: `POST /api/v1/data/ingest`
- **Rate Limit**: 1 request per 2 minutes (Anti-spam).
- **Format**: CSV file with columns matching the audit rules.

### C. Troubleshooting
To debug the server:
1.  **SSH into Server**:
    ```bash
    ssh root@10.14.190.28
    ```
2.  **Check Status**:
    ```bash
    docker ps
    # Look for container: drug_icd_mapping_prod_web_1
    ```
3.  **View Logs**:
    ```bash
    docker logs -f drug_icd_mapping_prod_web_1
    ```

## 5. Completed Tasks (As of Jan 20, 2026)
- [x] **Data Audit**: Rules implemented for 65k records.
- [x] **Database**: Created `drugs` and `diseases` tables; Normalized KB.
- [x] **API**: implemented `/consult_integrated` (Logic: TDV -> AI).
- [x] **Deployment**: Automated via GitHub Actions + Self-Hosted Runner.
- [x] **Security**: Rate Limiting for Ingest API.

## 6. Pending Tasks (Roadmap)
- [ ] **Schema Redesign**: Move to Star Schema for better analytics.
- [ ] **Logging**: Centralized monitoring for scrapers.
- [ ] **Scaling**: Apache Spark / Airflow integrations (Phase 2).
- [ ] **Intelligence**: Knowledge Graph construction (Phase 3).

## 7. Important Notes for New Maintainer
- **Server Environment**: The server has many other services. **ALWAYS** keep `COMPOSE_PROJECT_NAME=drug_icd_mapping_prod` in `deploy.yml` to avoid conflicts.
- **Database**: `medical.db` is NOT in Git (ignored). If the server DB is lost, use `scripts/upload_db.py` to restore from local backup.
- **Dependencies**: To add libraries, just update `requirements.txt` and Push. Build time will increase once (~5 mins).
