# EDIT-TEST LOOP WORKFLOW (Scaling Phase)

**Context:** Giai đoạn tối ưu hóa Search Engine & Xử lý Dữ liệu lớn (65k records).
**Mục tiêu:** Đảm bảo độ chính xác (Accuracy) và Hiệu năng (Performance).

## STEP 1: DEFINE BENCHMARK (Test Case)
- Xác định trường hợp cần test (Ví dụ: Lỗi chính tả "Paretamol", Thuốc mới "Sufentanil").
- Thêm case vào danh sách kiểm thử trong `scripts/benchmark_search.py`.
- Chạy: `python scripts/benchmark_search.py`.
- **Expect:** Kết quả hiện tại (có thể Fail hoặc Slow do Web Fallback).

## STEP 2: IMPLEMENT / OPTIMIZE (Code)
- **Logic:** Điều chỉnh `app/services.py` (Search Logic, Thresholds).
- **Index:** Nếu cần sửa cấu trúc tìm kiếm, update `run_import_datacore.py` và chạy lại Import.
- **Dependency:** Nếu thêm thư viện mới, update `requirements.txt` và chạy `docker-compose up -d --build`.

## STEP 3: VERIFY & MONITOR (Check)
- Chạy lại: `python scripts/benchmark_search.py`.
- **Target:**
    - Thời gian phản hồi < 1s (cho Data có sẵn).
    - Confidence score > 0.85 (Vector/Fuzzy).
- **Health Check:** Kiểm tra `docker stats` (RAM usage) và `docker-compose logs` để đảm bảo hệ thống ổn định.