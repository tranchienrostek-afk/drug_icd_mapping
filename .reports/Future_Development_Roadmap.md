# KẾ HOẠCH PHÁT TRIỂN & MỞ RỘNG HỆ THỐNG MAPPING DƯỢC PHẨM (FUTURE ROADMAP)

**Người lập:** AI Research Scientist (Dựa trên đánh giá của Senior Data Expert)
**Ngày lập:** 10/01/2026
**Mục tiêu:** Chuyển đổi từ công cụ tra cứu thuốc (Prototype) sang Nền tảng Dữ liệu Y tế Chuẩn Doanh nghiệp (Enterprise-grade Medical Data Platform).

---

## 1. Tầm nhìn Kiến trúc (Architectural Vision)

Hiện tại, hệ thống Version 2.0 hoạt động hiệu quả với 65,000 bản ghi nhờ tối ưu hóa In-Memory và Vector Search. Tuy nhiên, để đáp ứng khả năng mở rộng lên hàng triệu bản ghi và tích hợp đa nguồn dữ liệu trong tương lai, chúng ta cần tái cấu trúc theo hướng **Modern Data Stack** & **DataOps**.

### Sơ đồ chuyển đổi trạng thái:

| Đặc điểm | Hiện tại (Version 2.0) | Tương lai (Target State v3.0+) |
| :--- | :--- | :--- |
| **Lưu trữ** | CSV Flat Files | **Parquet (Storage) + Star Schema (SQL DB)** |
| **Xử lý** | Python Scripts (Pandas) | **Apache Spark (Distributed Computing)** |
| **Điều phối** | Chạy thủ công / Script rời rạc | **Apache Airflow (Workflow Orchestration)** |
| **Tìm kiếm** | In-Memory (FAISS/RapidFuzz) | **Disk-based Vector DB (Qdrant/Milvus)** |
| **Mô hình** | Mapping 1-1 đơn giản | **Knowledge Graph (Thuốc - Hoạt chất - Bệnh)** |
| **Chất lượng** | Kiểm tra thủ công | **Automated Data Quality (Great Expectations)** |

---

## 2. Các Trụ cột Phát triển Chiến lược

Kế hoạch dựa trên 3 trụ cột chính được đúc kết từ báo cáo đánh giá chuyên sâu:

### 2.1. Chuẩn hóa Mô hình Dữ liệu (Modeling Excellence)
*   **Chuyển đổi sang Star Schema:**
    *   Tách `drug_data` thành:
        *   `Fact_Drug_ICD_Mappings`: Bảng trung tâm lưu kết quả mapping.
        *   `Dim_Drugs`: Thông tin chi tiết thuốc (SDK, Nhà SX, Quy cách).
        *   `Dim_Ingredients`: Hoạt chất chuẩn hóa.
        *   `Dim_ICD10`: Danh mục bệnh lý quốc tế.
    *   **Lợi ích:** Tối ưu truy vấn báo cáo, dễ dàng mở rộng thêm các chiều dữ liệu mới (ví dụ `Dim_Pricing` - Lịch sử giá) mà không vỡ cấu trúc.

### 2.2. Tối ưu hóa Hiệu năng & Khả năng mở rộng (Scalability)
*   **Chiến lược Partitioning:** Phân vùng dữ liệu lớn theo `Năm` hoặc `Nhóm dược lý`. Giúp query chỉ quét <10% dữ liệu cần thiết thay vì 100%.
*   **Apache Spark Integration:** Sử dụng Spark cho các tác vụ nặng: Normalize tên thuốc, Re-indexing Vector hàng loạt. Giải quyết triệt để rủi ro tràn bộ nhớ (OOM).

### 2.3. DataOps & Tự động hóa (Automation)
*   **Airflow Orchestration:** Tự động hóa pipeline từ lúc Spider thu thập dữ liệu -> Cleaning -> Enrichment -> Indexing -> Audit.
*   **Data Audit & Lineage:** Tự động phát hiện dữ liệu rác (thiếu SDK, sai format) và truy vết nguồn gốc dữ liệu giúp debug nhanh chóng.

---

## 3. Lộ trình Triển khai (Implementation Roadmap)

### Giai đoạn 1: Gia cố nền tảng (Foundation Hardening) - Quý 1/2026
*   [x] **Task 1.1:** Xây dựng bộ quy tắc kiểm tra chất lượng dữ liệu (Data Audit) cho 65k bản ghi hiện tại.
*   [ ] **Task 1.2:** Thiết kế lại CSDL theo Star Schema. Migrade dữ liệu cũ sang cấu trúc mới.
*   [ ] **Task 1.3:** Triển khai Logging & Monitoring tập trung cho các Scraper.

### Giai đoạn 2: Mở rộng quy mô (Scale Out) - Quý 2/2026
*   [ ] **Task 2.1:** Tích hợp **Apache Spark** để xử lý Batch Processing.
*   [ ] **Task 2.2:** Chuyển đổi vector search sang **Qdrant** (Disk-based) để sẵn sàng cho 1 triệu thuốc.
*   [ ] **Task 2.3:** Triển khai **Apache Airflow** để điều phối pipeline tự động hàng ngày.

### Giai đoạn 3: Thông minh hóa (Intelligence & Graph) - Quý 3/2026+
*   [ ] **Task 3.1:** Xây dựng **Knowledge Graph** kết nối Thuốc - Tác dụng phụ - Chống chỉ định - Bệnh lý.
*   [ ] **Task 3.2:** Phát triển hệ thống gợi ý thuốc thay thế (Drug Substitution Recommender) dựa trên đồ thị tri thức.
*   [ ] **Task 3.3:** Tích hợp BI Dashboard (Superset/Metabase) để trực quan hóa dữ liệu y tế.

---

## 4. Kết luận

Việc tuân thủ lộ trình này sẽ biến hệ thống hiện tại từ một công cụ hỗ trợ tìm kiếm đơn thuần thành một **"Bộ não" dữ liệu dược phẩm (Pharma Data Brain)**. Hệ thống sẽ không chỉ trả lời câu hỏi *"Thuốc này mã ICD là gì?"* mà còn có thể tư vấn *"Thuốc này có thể thay thế bằng thuốc nào khác trong cùng nhóm điều trị?"* hoặc *"Xu hướng kê đơn cho nhóm bệnh này đang thay đổi ra sao?"*.

*File này đóng vai trò như kim chỉ nam kỹ thuật (Technical Compass) cho Professor AI trong các sprint tiếp theo.*
