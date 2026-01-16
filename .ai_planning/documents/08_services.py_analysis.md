# Phân Tích & Kế Hoạch Refactor `app/services.py`

File `app/services.py` hiện tại đang là một "God Object" (hơn 1500 dòng) chứa quá nhiều trách nhiệm: từ khởi tạo DB, migration, tìm kiếm (Fuzzy/Vector), đến quy trình duyệt thuốc (Staging). Điều này vi phạm nguyên tắc Single Responsibility Principle (SRP).

## 1. Hiện Trạng (Current State)

Class `DrugDbEngine` đang được sử dụng rộng rãi bởi:
- `app/api/drugs.py`: Tìm kiếm, tra cứu.
- `app/api/admin.py`: Duyệt staging.
- `app/api/data_management.py`: Import dữ liệu.
- `app/api/consult.py` & `analysis.py`: Tra cứu bổ trợ.

=> **Kết luận**: Code này **KHÔNG THỂ XOÁ NGAY**, vì nó là trái tim của hệ thống hiện tại. Tuy nhiên, cần phải **TÁCH (SPLIT)** khẩn cấp.

## 2. Kế Hoạch Xử Lý (Refactoring Plan)

Chúng ta sẽ chia nhỏ file này thành các module chuyên biệt trong thư mục `app/service/` và `app/database/`.

### Giai Đoạn 1: Tách Database Core
Chuyển phần khởi tạo kết nối và migration sang module riêng.
- **Mục tiêu**: `app/database/core.py`
- **Chức năng**:
    - `get_connection()`
    - `_ensure_tables()` (Chuyển thành script migration riêng hoặc chạy lúc startup).

### Giai Đoạn 2: Tách Search Engine
Logic tìm kiếm Fuzzy và Vector rất nặng và phức tạp, cần tách riêng.
- **Mục tiêu**: `app/service/drug_search_service.py`
- **Chức năng**:
    - `search_drug_smart()`
    - `_load_vector_cache()`
    - Logic TF-IDF và RapidFuzz.

### Giai Đoạn 3: Tách Quy Trình Staging (Workflow)
Logic duyệt/từ chối thuốc là nghiệp vụ quản trị, không nên dính với logic tìm kiếm.
- **Mục tiêu**: `app/service/drug_approval_service.py`
- **Chức năng**:
    - `save_verified_drug()`
    - `approve_staging()`
    - `reject_staging()`
    - `get_pending_stagings()`

### Giai Đoạn 4: Data Access Layer (Repository)
Các hàm CRUD cơ bản.
- **Mục tiêu**: `app/service/drug_repository.py`
- **Chức năng**:
    - `get_drug_by_id()`
    - `get_all_drugs()`

## Lộ Trình Thực Hiện (Roadmap)

1.  **Tạo các file mới** trong `app/service/` theo cấu trúc trên.
2.  **Copy code** từ `services.py` sang các file mới (giữ nguyên logic).
3.  **Sửa `services.py`**: Thay vì chứa logic, class `DrugDbEngine` sẽ import và gọi lại các service mới (Facade Pattern) để giữ tương thích ngược tạm thời.
4.  **Refactor API**: Dần dần sửa các file `app/api/*.py` để gọi trực tiếp service mới thay vì `DrugDbEngine`.
5.  **Xoá `services.py`**: Khi không còn API nào gọi đến nó nữa.
