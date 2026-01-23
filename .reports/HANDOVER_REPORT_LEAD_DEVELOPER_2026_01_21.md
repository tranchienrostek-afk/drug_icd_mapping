# 🏥 LEAD DEVELOPER HANDOVER REPORT (2026-01-21)

**Status:** Advanced Production Stable
**Version:** 2.1.0 (The "Fuzzy & Clean" Release)
**Author:** Antigravity (Lead AI Specialist)

---

## 🏗️ 1. CORE ARCHITECTURE DEEP DIVE

Hệ thống hiện tại không chỉ là một API gán nhãn, mà là một **Intelligent Medical Mapping Engine**. Bất kỳ ai kế nhiệm dự án này cần hiểu rõ cấu trúc "Dual-Service" sau:

### A. DrugSearchService (`app/service/drug_search_service.py`)
- **Mục tiêu:** Tìm kiếm thuốc chính xác trong danh mục 60k+ thuốc chính thức.
- **Chiến lược:** Exact (100%) -> LIKE (95%) -> RapidFuzz (88%) -> TF-IDF Vector (90%).
- **Sử dụng cho:** Autocomplete UI và API định danh thuốc.

### B. KBFuzzyMatchService (`app/service/kb_fuzzy_match_service.py`) [NEW]
- **Mục tiêu:** So khớp tên thuốc đầu vào (thường là "rác", sai chính tả) với **Knowledge Base** (600+ cặp tương tác đã duyệt).
- **Tại sao cần:** Tên thuốc trong KB có thể được lưu ở dạng khác với danh mục chính thức (do TĐV nhập tay). Cơ chế Fuzzy Match giúp tăng tỷ lệ khớp lên ~30% so với Exact Match.
- **Features:** Có cơ chế **Auto-Refresh** (tự nạp lại vào RAM sau khi ingest dữ liệu mới).

---

## 📊 2. DATA SCHEMA EVOLUTION

### Bảng `diseases` (Thay thế cách lưu cũ)
Chúng ta đã chuyển từ việc dùng chung bảng `knowledge_base` cho Disease sang bảng `diseases` chuẩn (Spec 02):
- **Columns:** `id` (UUID), `icd_code`, `disease_name`, `chapter_name`, `slug`, `search_text`, `is_active`.
- **Optimization:** Có FTS5 (`diseases_fts`) để search tên bệnh cực nhanh.
- **Import:** Luôn chạy `python import_diseases.py` sau khi cập nhật `icd_data.csv`.

---

## 🧠 3. "AI" ALGORITHMS EXPLAINED

Dự án sử dụng **Hybrid Intelligence** thay vì dùng LLM trực tiếp (để tiết kiệm $ và tăng tốc):

### TF-IDF + Cosine Similarity
- Sử dụng `TfidfVectorizer` của `sklearn` để biến tên thuốc thành vector.
- Giúp tìm thấy "Ludox 200mg" khi user nhập "200mg Ludox" (LLM-like behavior nhưng chạy nội bộ).

### RapidFuzz (String Similarity)
- Dùng `fuzz.token_sort_ratio` để bỏ qua sự sai khác về số 0, dấu cách hoặc gạch ngang.
- **Threshold:** 70% là điểm ngọt (sweet spot) được kiểm nghiệm.

---

## 🛠️ 4. QUY TRÌNH VẬN HÀNH (FOR OPS)

### Nạp dữ liệu mới (Ingest)
1.  Gửi file CSV qua `POST /api/v1/data/ingest`.
2.  Hệ thống chạy ETL trong Background.
3.  **CRITICAL:** ETL xong sẽ tự gọi `refresh_cache()` của Fuzzy Matcher. Bạn không cần restart server.

### Deploy thủ công (Nếu CI/CD lỗi)
```bash
ssh root@10.14.190.28
cd /root/workspace/drug_icd_mapping/fastapi-medical-app
git pull
docker-compose up -d --build
```

---

## ☢️ 5. "CẠM BẪY" CẦN TRÁNH (WATCH OUT!)

1.  **SQLite Row Factory:** `db.get_connection()` trả về `Row` object (dict-like). Nếu bạn dùng `sqlite3.connect()` trực tiếp, nó trả về `tuple`. **Cẩn thận khi truy cập `row[0]` vs `row['column']`**.
2.  **Rate Limit:** API Ingest bị giới hạn 1 request/2 phút. Nếu test, hãy đợi hoặc chỉnh sửa `app/api/data_management.py`.
3.  **Docker Volumes:** Database `medical.db` nằm trong volume Docker. Khi rebuild container, data được bảo toàn. Nếu muốn xóa trắng database, phải chạy `docker-compose down -v`.

---

## 📈 6. KẾ HOẠCH PHÁT TRIỂN TIẾP THEO

- [ ] **Embedding Search:** Chuyển từ TF-IDF sang `all-MiniLM-L6-v2` (Vector Database) nếu list thuốc lên > 1 triệu bản ghi.
- [ ] **Synonym Mapping:** Xây dựng bảng `drug_synonyms` (vd: `vit` <-> `vitamin`).
- [ ] **Disease Mapping Quality:** Áp dụng Fuzzy Match tương tự cho ICD Code (hiện tại ICD vẫn đang exact match).

---
**Tài liệu tham khảo chính:**
- `DOCS/`: Folder chứa Spec thiết kế.
- `.issues/`: Theo dõi các bug đã fix (đặc biệt là BUG-017).
- `walkthrough.md`: Hướng dẫn các tính năng mới nhất.

*Chúc người kế nhiệm may mắn, hệ thống này rất mạnh mẽ nếu được bảo trì đúng cách!* 🚀
