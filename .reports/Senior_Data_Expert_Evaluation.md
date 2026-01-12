# Báo cáo Đánh giá Chuyên sâu (Senior Data Expert Report) - Dự án ANAC Data Pipeline

**Người lập:** Chuyên gia Dữ liệu Cao cấp (Senior Data Expert)  
**Dự án:** Hệ thống xử lý dữ liệu hàng không ANAC (25 năm)  
**Ngày đánh giá:** 10/01/2026

---

## 1. Tổng quan hệ thống (Executive Summary)
Dự án ANAC được xây dựng dựa trên kiến trúc **Modern Data Stack (MDS)** với tư duy **DataOps** hiện đại. Hệ thống sử dụng mô hình kiến trúc Medallion (Bronze-Silver-Gold) phối hợp với các công cụ mã nguồn mở mạnh mẽ nhất hiện nay (Airflow, Spark, Docker). Dưới góc độ chuyên gia, đây là một thiết kế chuẩn mực cho phân tích dữ liệu quy mô lớn.

---

## 2. Phân tích Ưu điểm (Strengths)

### 2.1. Kiến trúc lưu trữ tối ưu (Modern Storage Layer)
*   **Columnar Storage (Parquet):** Việc chọn định dạng Parquet thay vì CSV truyền thống cho thấy sự am hiểu về hiệu năng. Nó giúp giảm thiểu I/O disk và tối ưu hóa chi phí lưu trữ/tính toán.
*   **Partitioning Strategy:** Hệ thống thực hiện phân vùng (Partitioning) theo `Năm/Tháng` tại tầng Silver. Đây là kỹ thuật sống còn để đảm bảo tốc độ truy vấn không bị suy giảm theo thời gian khi dữ liệu tích lũy thêm hàng chục năm.

### 2.2. Khả năng mở rộng bền bỉ (Scalability & Orchestration)
*   **Apache Spark Integration:** Sử dụng Spark để xử lý dữ liệu thay vì thuần Python/Pandas cho phép hệ thống có khả năng xử lý hàng chục GB dữ liệu mà không lo bị nghẽn bộ nhớ (OOM).
*   **Robust Workflow (Airflow):** Pipeline được điều phối qua Airflow giúp quản lý trạng thái, lịch trình và cơ chế thử lại (Retry) cực kỳ chuyên nghiệp, đảm bảo tính liên tục của dữ liệu.

### 2.3. Thiết kế mô hình dữ liệu chuẩn (Modeling Excellence)
*   **Star Schema implementation:** Việc tách biệt bảng Fact và Dimension tại tầng Gold là một bước tiến từ "dữ liệu phẳng" sang "tài sản thông tin". Cấu trúc này tối ưu tuyệt đối cho các công cụ BI hiện đại như Power BI, Tableau hay Looker.
*   **Data Enrichment:** Tích hợp các chiều thông tin như ngày lễ (holidays) và mùa vụ (seasons) cho thấy tư duy phân tích sâu sắc, giúp khám phá được các yếu tố ngoại vi tác động đến kinh doanh.

### 2.4. Môi trường đóng gói hoàn hảo (Containerization)
*   Việc sử dụng Docker đảm bảo hệ thống có thể triển khai (Deploy) ngay lập tức trên bất kỳ hạ tầng nào (On-premise hay Cloud) mà không gặp lỗi "máy tôi chạy được nhưng máy bạn thì không".

---

## 3. Phân tích Nhược điểm & Hạn chế (Weaknesses & Limitations)

### 3.1. Thiếu hụt cơ chế Kiểm soát chất lượng (Data Quality - DQ)
*   Hiện tại pipeline tập trung nhiều vào việc "chuyển đổi" (Transformation) nhưng chưa có các bước "kiểm tra" (Validation) tự động. Nếu dữ liệu nguồn từ ANAC bị đổi cấu trúc đột ngột, hệ thống có thể gặp lỗi mà không có cảnh báo sớm (Data Contract issues).

### 3.2. Rủi ro về "Single Point of Failure" trong thu thập
*   Quy trình `download_csv` dựa vào việc Web Scraping thủ công. Trang web của chính phủ thường thay đổi giao diện/cấu trúc link, điều này có thể làm gãy pipeline nếu không có cơ chế giám sát hoặc API dự phòng.

### 3.3. Bảo mật thông tin nhạy cảm (Security Concerns)
*   Thông tin kết nối cơ sở dữ liệu và Fernet key của Airflow đang được cấu hình cứng (hardcoded) hoặc để mặc định trong tệp `docker-compose`. Đối với môi trường doanh nghiệp, đây là một rủi ro bảo mật nghiêm trọng.

### 3.4. Metadata Management
*   Hệ thống chưa có bộ từ điển dữ liệu (Data Catalog) hoặc công cụ theo dõi dòng chảy dữ liệu (Data Lineage) tự động. Khi số lượng bảng tăng lên, việc quản lý sẽ trở nên khó khăn cho người dùng cuối.

---

## 4. Khuyến nghị cấp cao (Senior Recommendations)

1.  **Triển khai Unit Testing cho Dữ liệu:** Tích hợp thư viện như **Great Expectations** hoặc **dbt tests** để kiểm tra tính đúng đắn của dữ liệu ngay sau mỗi bước xử lý.
2.  **Externalizing Configuration:** Chuyển toàn bộ biến môi trường, mật khẩu vào các hệ thống quản lý bí mật (Secrets Management) như HashiCorp Vault hoặc AWS Secrets Manager.
3.  **Hệ thống Cảnh báo (Alerting):** Cấu hình Airflow gửi thông báo qua Slack/Email ngay khi có một task bị thất bại để đội ngũ kỹ thuật phản ứng tức thì.
4.  **Xây dựng tầng Semantic:** Cân nhắc sử dụng thêm công cụ như dbt để quản lý tầng biến đổi dữ liệu (Transformation logic) một cách tập trung và dễ bảo trì hơn.

## 5. Bài học kinh nghiệm cho dự án Mapping Thuốc (Lessons Learned)
Dựa trên các phân tích cho dự án ANAC, dưới đây là các bài học có thể áp dụng trực tiếp để nâng cấp hệ thống `drug_icd_mapping`:

1.  **Nâng cấp chất lượng dữ liệu (Data Quality - DQ):**
    - Cần xây dựng bộ kiểm định tự động (Data Audit) để phát hiện các bản ghi thiếu thông tin quan trọng (Hoạt chất, SDK) ngay khi nhập liệu.
    - Giám sát tỷ lệ ánh xạ thành công giữa Thuốc và ICD-10 để cảnh báo sớm khi chất lượng dữ liệu nguồn suy giảm.

2.  **Tăng cường khả năng chống chịu của hệ thống Thu thập (Scraping Resilience):**
    - Triển khai cơ chế giám sát (Monitoring) tỷ lệ thành công của các scraper hàng ngày.
    - Xây dựng cơ chế dự phòng (Fallback) khi các trang web nguồn (Như trungtamthuoc, thuocbietduoc) thay đổi cấu trúc giao diện.

3.  **Tối ưu hóa kiến trúc lưu trữ:**
    - Xem xét sử dụng định dạng Parquet cho các tệp dữ liệu trung gian khi xử lý hàng loạt (Bulk processing) để tối ưu hiệu năng I/O so với CSV truyền thống.

4.  **Chuyên nghiệp hóa quản lý Bảo mật:**
    - Chuyển đổi từ cấu hình cứng sang sử dụng biến môi trường (Environment Variables) triệt để và ứng dụng các hệ thống quản lý bí mật (Secrets Management) cho môi trường Production.

5.  **Minh bạch hóa Dòng chảy dữ liệu (Data Lineage):**
    - Tài liệu hóa quy trình biến đổi dữ liệu từ khâu thu thập thô đến khi ra kết quả mã ICD-10 cuối cùng để dễ dàng truy vết và sửa lỗi (Debugging).

6.  **Tối ưu hóa mô hình dữ liệu theo hướng Star Schema:**
    - Thay vì lưu trữ dữ liệu "phẳng" (Flat table) chứa tất cả thông tin thuốc, hoạt chất và ICD, cần tách biệt rõ ràng thành:
        - **Bảng Fact:** Lưu trữ các giao dịch/kết quả mapping (ví dụ: `Drug_ICD_Mappings`).
        - **Bảng Dimension:** Lưu trữ thông tin chi tiết các thực thể (ví dụ: `Dim_Drugs`, `Dim_ICD10`, `Dim_Ingredients`).
    - Việc áp dụng Star Schema giúp hệ thống dễ dàng mở rộng khi cần tích hợp thêm các chiều thông tin mới như: Nhóm dược lý, Đơn vị sản xuất, hoặc Lịch sử thay đổi mà không làm chậm tốc độ truy vấn tìm kiếm chính.

7.  **Áp dụng Orchestration (Airflow) và Big Data Processing (Apache Spark):**
    - **Apache Spark:** Khi quy mô dữ liệu thuốc tăng lên (không chỉ 65k mà có thể là hàng triệu bản ghi từ nhiều nguồn khác nhau), Spark sẽ giúp xử lý làm sạch, chuẩn hóa và tính toán vector search song song, tránh nghẽn bộ nhớ (OOM) mà Python thuần thường gặp phải.
    - **Apache Airflow:** Thay vì chạy các script thủ công, Airflow sẽ điều phối toàn bộ workflow: `Scraping` -> `Normalization` -> `Vector Indexing` -> `Quality Audit`.
    - **Cơ chế Retry & Alerting:** Airflow tự động chạy lại các task Scraping bị lỗi do mạng và gửi cảnh báo ngay lập tức nếu một bước trong pipeline mapping bị gián đoạn, đảm bảo dữ liệu luôn được cập nhập đúng hạn.

8.  **Chiến lược Phân vùng dữ liệu (Partitioning Strategy):**
    - **Tối ưu truy vấn:** Đối với dữ liệu thuốc ngày càng lớn, việc áp dụng Partitioning (ví dụ theo `Nhóm dược lý` hoặc `Năm cập nhật`) giúp hệ thống chỉ quét (scan) các phân vùng cần thiết thay vì toàn bộ database, giảm đáng kể thời gian tìm kiếm.
    - **Quản lý vòng đời dữ liệu:** Phân vùng giúp việc lưu trữ (Archiving) hoặc xóa dữ liệu cũ/lỗi thời trở nên dễ dàng và nhanh chóng hơn bằng cách thao tác trên từng phân vùng thay vì từng dòng dữ liệu.
    - **Xử lý song song:** Kết hợp với Spark, Partitioning cho phép chia nhỏ dữ liệu để xử lý song song trên nhiều lõi (cores) hiệu quả hơn, cực kỳ hữu ích khi thực hiện Re-indexing cho Vector Search trên quy mô lớn.

9.  **Thiết kế mô hình dữ liệu chuẩn (Modeling Excellence):**
    - **Tư duy từ Dữ liệu phẳng sang Tài sản thông tin:** Cần chuyển đổi cách lưu trữ từ các tệp Excel/CSV rời rạc sang mô hình quan hệ chặt chẽ. Việc tách biệt bảng Fact (biến động) và Dimension (ít biến động) giúp dữ liệu không chỉ để "lưu" mà còn để "phân tích" chuyên sâu.
    - **Làm giàu dữ liệu (Data Enrichment):** Không chỉ dừng lại ở `Tên thuốc` và `ICD`, cần tích hợp thêm các "chiều" thông tin bổ trợ như:
        - Thông tin dược lý mở rộng.
        - Tương tác thuốc.
        - Phân nhóm bệnh lý theo chương (ICD Chapters).
    - **Sẵn sàng cho BI (Business Intelligence):** Mô hình chuẩn hóa giúp việc kết nối với các công cụ như Power BI, Tableau để trực quan hóa tỷ lệ ánh xạ, xu hướng sử dụng thuốc theo nhóm bệnh trở nên cực kỳ đơn giản và mạnh mẽ.

---

## 6. Đánh giá chung (Final Verdict)
**Điểm số: 8.5/10**  
Dự án ANAC là một hình mẫu xuất sắc về mặt kỹ thuật và kiến trúc. Các nhược điểm nêu trên chủ yếu thuộc về khâu vận hành quy mô lớn (Enterprise Grade). Với cấu trúc hiện tại, hệ thống hoàn toàn đủ khả năng trở thành nền tảng dữ liệu tin cậy cho bất kỳ doanh nghiệp vận tải/hàng không nào.

---
*Báo cáo được phê duyệt để lưu chuyển nội bộ.*
