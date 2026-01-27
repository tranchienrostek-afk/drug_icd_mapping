# Nhật ký bàn giao dự án: Drug ICD Mapping System
**Ngày**: 27/01/2026
**Người viết**: AI Assistant (Antigravity)
**Người nhận**: Lead Engineer (Next Shift)

---

## 👋 Lời mở đầu
Chào người anh em thiện lành! Mai tôi nghỉ phép rồi. Dự án **Drug ICD Mapping** vừa trải qua một đợt "đại phẫu" chuyển từ SQLite sang PostgreSQL. Mọi thứ đang chạy rất mượt, nhưng để ông không bị "ngợp" khi tiếp nhận, tôi đã ghi lại chi tiết mọi thứ ở đây. Đọc kỹ nhé, xương máu cả đấy!

---

## 🛑 Những sai lầm tôi đã mắc phải (Và đã sửa)
Để ông không dẫm vào vết xe đổ, tôi thú tội trước những chỗ tôi đã làm ẩu và cách tôi fix nó:

### 1. Hardcode SQL Syntax (Cú pháp `?` vs `%s`)
*   **Lỗi**: Tôi đã viết hàng tấn câu query dùng `?` (kiểu SQLite) trong code cũ. Khi chuyển sang Postgres (`psycopg2`), nó báo lỗi syntax đầm đìa vì Postgres đòi `%s`.
*   **Fix**: Thay vì sửa tay 1000 chỗ, tôi đã viết một cái **Wrapper thần thánh** tên là `PostgresCursorWrapper` trong `app/database/core.py`. Nó tự động regex replace `?` thành `%s` trước khi execute.
*   **Lưu ý**: Nếu ông viết query mới, hãy cứ dùng `%s` cho chuẩn Postgres, nhưng nếu lỡ tay dùng `?` thì Wrapper vẫn cân được.

### 2. Bypass Abstraction Layer
*   **Lỗi**: Trong `KBFuzzyMatchService` và `DrugMatcher`, tôi (hoặc ai đó) đã `import sqlite3` và connect thẳng vào file DB. Hậu quả là khi đổi sang Postgres server, mấy service này vẫn cứ đi tìm file `.db` cũ rích.
*   **Fix**: Tôi đã refactor toàn bộ service để dùng `DatabaseCore`. Giờ tụi nó gọi `db_core.get_connection()` và hệ thống tự điều phối connection string.
*   **Bài học**: **CẤM** import `sqlite3` trực tiếp nữa nhé!

### 3. Context Manager (`with ... as cursor`)
*   **Lỗi**: Script migration chết giữa chừng vì cái Wrapper của tôi thiếu hàm `__enter__` và `__exit__`.
*   **Fix**: Đã bổ sung đầy đủ. Giờ ông có thể dùng `with core.get_connection() as conn:` thoải mái.

### 4. Deploy Ẩu
*   **Lỗi**: Script cũ `deploy_auto.py` dùng `sftp` để upload file local DB lên server. Tư duy này sai bét với Production DB (Postgres).
*   **Fix**: Đã vứt script đó. Thay bằng `deploy_prod.sh` (Git Pull + Docker Build) và dùng `entrypoint.sh` để tự động chạy migration khi container khởi động.

---

## 🚀 Tình hình hiện tại (Status Quo)
Dự án đang ở trạng thái **STABLE** (Ổn định) sau khi migrate.

*   **Database**: PostgreSQL 15 (Chạy Docker hoặc Server Host).
*   **Data**: Đã chuyển đổi thành công **65,403** bản ghi thuốc.
*   **Search Engine**: Đã có cột `search_vector` (tsvector) để chạy Full Text Search xịn sò, không còn phụ thuộc vào `FTS5` chậm chạp của SQLite nữa.
*   **APIs**:
    *   `/ingest`: Đã test, ghi data ầm ầm vào Postgres.
    *   `/match_v2`: Chạy ngon với thuật toán Vector/Fuzzy mới.
    *   `/consult`: Đã tương thích hoàn toàn.
*   **Test**: Đã verify row count khớp 100%.

---

## 📅 Kế hoạch làm việc (Action Plan) cho người tiếp nhận

Ông làm ơn follow checklist này giúp tôi nhé:

### 1. Ưu tiên cao (Làm ngay hôm nay/mai)
- [ ] **Deploy Production**:
    - Commit code hiện tại lên GitHub (`git push origin main`).
    - SSH vào server, chạy `./deploy_prod.sh`.
    - Gọi `/api/v1/health` để chắc chắn DB xanh lè.
- [ ] **Check Port Conflict**:
    - Nếu server đã có Postgres (port 5432), nhớ sửa `docker-compose.yml` đổi port mapping thành `5435:5432` kẻo conflict nhé. Tôi đã note kỹ trong `task_044_migrate_data.md`.

### 2. Ưu tiên trung bình (Tuần sau)
- [ ] **Tối ưu Index**:
    - Hiện tại tôi mới chỉ đánh index cơ bản. Ông nên chạy `EXPLAIN ANALYZE` vào mấy query search trong `DrugSearchService`. Nếu thấy chậm, táng thêm index GIN vào cột `search_vector`.
- [ ] **Move Agent Data**:
    - API `/agent-search` đang trả về JSON raw và chưa lưu DB. Ông nên tạo bảng `agent_crawl_results` trong Postgres để lưu lại lịch sử tìm kiếm này (cache lại đỡ tốn tiền OpenAI).

### 3. Dài hạn (Tech Debt)
- [ ] **Redis Caching**:
    - Fuzzy Matching (RapidFuzz) vẫn đang load 65k tên thuốc vào RAM mỗi lần init. Hơi tốn RAM. Ông nên cài Redis để cache cái list này, hoặc dùng `pg_trgm` extension của Postgres để search fuzzy trực tiếp trong DB luôn (đỡ phải load vào RAM python).

---

## 📂 Tài liệu tham khảo
Tôi để hết "bí kíp" ở đây:
1.  `postgres_setup_guide.md`: Hướng dẫn cài Postgres cho người mới.
2.  `api_audit.md`: Danh sách API nào dùng bảng nào.
3.  `task_044_migrate_data.md`: Báo cáo chi tiết vụ migrate vừa rồi.

Chúc ông may mắn! Code tôi viết clear lắm, chắc không bug đâu (hy vọng thế). 😉

*Ký tên,*
**Antigravity**
