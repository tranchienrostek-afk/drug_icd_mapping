# 🎓 DevOps & Backend Learning Roadmap - Drug ICD Mapping System
**Phiên bản:** 1.0 | **Ngày tạo:** 2026-01-27

---

## 📌 Giới thiệu
Tài liệu này cung cấp lộ trình học tập chi tiết để một sinh viên có thể tiếp nhận, vận hành và phát triển hệ thống **Drug ICD Mapping**. Lộ trình đi từ kiến thức nền tảng đến các kỹ năng chuyên sâu được sử dụng trong dự án.

## 🏗️ Kiến trúc & Tech Stack
Dự án sử dụng mô hình **Microservices-oriented** với các thành phần chính:
- **Ngôn ngữ:** Python 3.10+ (FastAPI)
- **Database:** PostgreSQL (Production), SQLite (Dev)
- **AI Integration:** Azure OpenAI (GPT-4)
- **Deployment:** Docker, Docker Compose, Nginx Reverse Proxy
- **CI/CD:** GitHub Actions (Self-hosted Runners)

---

## 🗺️ Lộ trình học tập (Learning Path)

### Giai đoạn 1: Nền tảng (Foundation) - 2 Tuần
*Mục tiêu: Hiểu cách code chạy và môi trường cơ bản.*

#### 1. Python & FastAPI Core
- **Kiến thức cần học:**
  - Python async/await (`async def`).
  - Pydantic models (Data validation).
  - FastAPI Dependency Injection (`Depends`).
  - Type hints trong Python.
- **Thực hành dự án:**
  - Đọc hiểu `app/models.py` (Pydantic models).
  - Xem `app/api/drugs.py` để hiểu cách viết API endpoint.
- **Tài liệu tham khảo:** FastAPI Docs, Python AsyncIO.

#### 2. Containerization (Docker)
- **Kiến thức cần học:**
  - Docker basics: Image, Container, Volume, Network.
  - `Dockerfile`: Multi-stage build (đang dùng để tối ưu).
  - `docker-compose`: Quản lý multi-containers.
- **Thực hành dự án:**
  - Chạy local dev bằng `docker-compose up`.
  - Hiểu file `Dockerfile` và `docker-compose.yml`.
  - Fix lỗi cổng `8000` bị chiếm dụng.

---

### Giai đoạn 2: Backend Development - 3 Tuần
*Mục tiêu: Có thể thêm feature mới và fix bug.*

#### 3. Database Management (PostgreSQL & SQLite)
- **Kiến thức cần học:**
  - SQL Queries cơ bản & Indexing.
  - Sự khác biệt giữa SQLite (file-based) & PostgreSQL (server-based).
  - Kết nối DB trong Python (`psycopg2`, `sqlite3`).
  - Data Migration (chuyển đổi data giữa các hệ quản trị).
- **Thực hành dự án:**
  - Đọc script `scripts/migrate_data_to_postgres.py` để hiểu cách xử lý data mismatch (UUID vs Integer).
  - Thực hành backup/restore PostgreSQL bằng `pg_dump`.

#### 4. Testing (Pytest)
- **Kiến thức cần học:**
  - Unit Test vs Integration Test.
  - `pytest` framework.
  - `pytest-mock` để mock database/API calls.
  - `pytest-asyncio` cho test async code.
- **Thực hành dự án:**
  - Chạy bộ test hiện tại: `pytest unittest/`.
  - Viết test case mới cho một API đơn giản.

#### 5. AI Integration (Azure OpenAI)
- **Kiến thức cần học:**
  - Mô hình gọi API LLM (Request/Response).
  - Prompt Engineering cơ bản.
  - Xử lý Env vars an toàn.
- **Thực hành dự án:**
  - Xem `app/mapping_drugs/ai_matcher.py`.
  - Hiểu cách cấu hình API Key từ `.env` (không hardcode).

---

### Giai đoạn 3: DevOps & Operations - 3 Tuần
*Mục tiêu: Deploy code lên server, giám sát và xử lý sự cố.*

#### 6. Linux & Server Administration
- **Kiến thức cần học:**
  - Linux commands cơ bản (`ls`, `cd`, `grep`, `tail`, `chmod`, `chown`).
  - Quản lý process (`ps`, `htop`, `screen`, `nohup`).
  - SSH & SCP (Remote access).
  - File permission (Lỗi 403 thường gặp).
- **Thực hành dự án:**
  - SSH vào server staging.
  - Xem logs container: `docker logs -f <container_name>`.
  - Chỉnh sửa file config trên server bằng `nano`/`vim`.

#### 7. CI/CD (GitHub Actions)
- **Kiến thức cần học:**
  - Automation Workflow (YAML).
  - Self-hosted Runner (Server tự build code).
  - Pipeline stages: Test → Build → Deploy.
- **Thực hành dự án:**
  - Đọc file `.github/workflows/deploy.yml`.
  - Hiểu cách GitHub trigger server chạy lệnh `git pull` và `docker-compose up`.

#### 8. Nginx & Reverse Proxy
- **Kiến thức cần học:**
  - Concept Reverse Proxy.
  - Routing domain -> port (80 -> 8000).
  - SSL/HTTPS certificate.
- **Thực hành dự án:**
  - Hiểu sơ đồ mapping: Request -> Nginx -> Docker Container (Port 8000).

---

## 🛠️ Bài học thực tế từ dự án (Case Studies)

### Case 1: Data Migration Fail (SQLite -> Postgres)
- **Vấn đề:** SQLite chấp nhận UUID vào cột Integer, Postgres thì không.
- **Bài học:** Data type strictness. Luôn validate data trước khi insert.
- **Kỹ năng:** Viết script migration Python, Clean data.

### Case 2: Deployment Conflict
- **Vấn đề:** Deploy thất bại do tên container trùng lặp.
- **Bài học:** Docker container lifecycle. Cần remove container cũ trước khi tạo mới (`docker rm -f`).
- **Kỹ năng:** Docker commands, Shell scripting.

### Case 3: AI Model không chạy
- **Vấn đề:** Restart container nhưng code/env mới không cập nhật.
- **Bài học:** Container immutability. Thay đổi env phải recreate container (`docker-compose up -d`), không chỉ restart.
- **Kỹ năng:** Hiểu sâu về Docker runtime.

---

## 📚 Tài liệu khuyên đọc (Resources)
1. **FastAPI Modern Python Web Development** (Sách/Doc)
2. **Dive Into Docker** (Khóa học/Video)
3. **PostgreSQL High Performance** (Sách - nâng cao)
4. **GitHub Actions Documentation**
5. **Dự án hiện tại:** Đọc kỹ `Deployment & Operations Guide.md` (Đây là "Kinh thánh" của dự án).

---
*Lộ trình được thiết kế bám sát thực tế vận hành hệ thống Drug ICD Mapping.*
