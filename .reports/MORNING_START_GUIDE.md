# 🌅 MORNING START GUIDE (Ngày mới năng lượng!)
**Last Updated:** 2026-01-20 (End of Day)

## 1. Tình Trạng Hiện Tại (Status)
Hệ thống **Medical Consultation** đang chạy ổn định trên **Server Dev (10.14.190.28)**.

| Thành phần | Trạng thái | Ghi chú |
| :--- | :--- | :--- |
| **API Server** | 🟢 **RUNNING** | Port 8000. Đã bật CI/CD tự động. |
| **Database** | 🟢 **LOADED** | Đã nạp full dữ liệu. `check_db` OK. |
| **Ingest API** | 🟢 **SECURED** | Đã thêm Rate Limit (1 req / 2 phút). |
| **Consult API** | 🟢 **READY** | Logic: Ưu tiên TDV -> AI Suggestion. |

## 2. Hôm Qua Bạn Đã Làm Gì? (Yesterday's Wins)
1.  **Fixed Deploy**: Chuyển sang GitHub Actions Self-Hosted (Runner `Nifi`). Code tự update sau 2 phút khi Push.
2.  **Fixed ETL**: Sửa logic file CSV, mapping cột `?column?` thành `Tên thuốc` tự động.
3.  **Security**: Chặn spam API upload dữ liệu.
4.  **Documentation**: Đã có Swagger UI và Walkthrough đầy đủ.

## 3. Việc Cần Làm Sáng Mai (To-Do List)
Khi bạn ngồi vào bàn làm việc, hãy:

1.  **Kiểm tra Server**:
    Mở terminal và chạy lệnh:
    ```bash
    ssh root@10.14.190.28 "docker ps"
    ```
    *Kỳ vọng: Thấy container `drug_icd_mapping_prod_web_1` đang Up.*

2.  **Check Log qua đêm**:
    Xem có ai spam hay lỗi gì không:
    ```bash
    ssh root@10.14.190.28 "docker logs --tail 100 drug_icd_mapping_prod_web_1"
    ```

3.  **Tiếp tục Task 1.3**:
    Mục tiêu tiếp theo trong `task.md` là **Centralized Logging**.
    *   Nghiên cứu cách gom log từ các Scraper về một chỗ (ELK Stack hoặc đơn giản là file log tập trung).

## 4. Tài Liệu Cần Đọc (Nếu quên)
-   `walkthrough.md`: Hướng dẫn sử dụng hệ thống.
-   `task.md`: Danh sách công việc còn lại.
-   `.reports/HANDOVER_REPORT_2026_01_20.md`: Báo cáo chi tiết kỹ thuật.

---
**Chúc bạn một ngày làm việc hiệu quả! ☕**
