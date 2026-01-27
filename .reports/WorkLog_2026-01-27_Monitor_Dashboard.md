# 📋 WorkLog 2026-01-27 - Monitor Dashboard & Bug Fixes

> **Ngày:** 2026-01-27 | **Author:** AI Assistant

---

## ✅ Công việc hoàn thành

### 1. Fix Unit Test - Default Role Logic
- **File:** `unittest/test_consult_tdv_fallback.py`
- **Commit:** `745d5f2`
- **Nội dung:** Cập nhật test `test_both_null_defaults_to_main_drug` để expect `validity='valid'`, `role='main drug'`, `source='INTERNAL_KB_DEFAULT'` phù hợp logic mới

---

### 2. Nâng cấp Monitor Dashboard
- **Commit:** `83508d9`

#### Backend (`app/monitor/service.py`)
- Thêm hàm `get_detailed_system_stats()` với thông tin:
  - CPU: percent, cores, logical cores, frequency
  - Memory: total, available, used, percent
  - Disk: total, used, free, percent
  - Network: bytes_sent, bytes_recv, packets
  - Uptime: boot_time, uptime_seconds, uptime_formatted
  - Process: cpu, ram, threads

#### API (`app/monitor/router.py`)
- Endpoint mới: `GET /api/v1/monitor/system`

#### Frontend (`app/monitor/static/index.html`)
- **Tab mới: "💻 System"** với:
  - Gauge charts cho CPU, RAM, Disk
  - Server uptime và boot time
  - Network I/O statistics
  - App process stats

---

### 3. Viết lại Deployment & Operations Guide
- **File:** `.reports/Deployment & Operations Guide.md`
- **Commit:** `6fcdb58`
- **Triết lý mới:** "🌊 Push to Git, Everything Flows"
- **Nội dung:**
  - Mô tả CI/CD pipeline tự động
  - Loại bỏ các bước thủ công không cần thiết
  - Thêm URLs quan trọng và commands emergency
  - Cập nhật monitoring dashboard info

---

### 4. Fix MonitorService PostgreSQL Compatibility
- **File:** `app/service/monitor_service.py`
- **Commit:** `1c9ce46`
- **Bug:** `sqlite3.Row` không hoạt động với PostgreSQL
- **Fix:**
  - Bỏ `conn.row_factory = sqlite3.Row`
  - Thêm logic nhận diện `db_type` (postgres/sqlite)
  - Sử dụng placeholder phù hợp (`%s` vs `?`)
  - Xử lý kết quả dict/tuple đúng cách

---

## 📊 Commits Summary

| Commit | Message |
|--------|---------|
| `745d5f2` | test: update test to match new default main drug logic |
| `83508d9` | feat: enhanced monitor dashboard with System tab |
| `6fcdb58` | docs: rewrite Deployment Guide with Push-to-Git philosophy |
| `1c9ce46` | fix: MonitorService compatible with PostgreSQL |

---

## 🔗 Links

- **Production Dashboard:** http://10.14.190.28:8000/monitor
- **Admin Portal:** http://10.14.190.28:8000/
- **GitHub Actions:** Check CI/CD pipeline status

---

*Báo cáo tự động tạo bởi AI Assistant*
