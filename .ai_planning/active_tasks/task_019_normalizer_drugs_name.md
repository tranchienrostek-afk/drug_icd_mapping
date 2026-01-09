# TASK TICKET: [TASK_019] - [Chuẩn hoá tên thuốc theo từng quá trình]

**Status:** Done
**Người Tạo: Trần Văn Chiến**

Ngày tạo: 09.01.2026 15:36

## 1. Mục tiêu (Objective)

Chú ý với bài toán search và bài toán fuzzy map (bm25) hay vector
embedding  thì dùng 2 bộ normalize khác
nhau

Thuật toán chuẩn hoá tên thuốc để search thì theo bộ : C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\drug_normalizer.py

Thuật toán chuẩn hoá tên thuốc cho bài toán fuzzy map (bm25) hay vector trong database thì dùng chương trình normalizer cũ, được lưu tại: C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\draft_normalization_rules.py

2 file đó đặt tên hơi buồn cười, sửa lại tên chút nhé, tuyệt đối không động đến nội dung bên trong của 2 file đó.

Nhắc lại quy trình tìm kiếm.

Quy trình

Bước 1: Tìm thuốc trong cơ sở dữ liệu.

Chuẩn hoá tên thuốc

Tìm chính xác

Tìm theo fuzzy map, tìm theo vector

Độ chính xác lớn (Ví dụ trên 0.7. Thì lấy thông
tin)

 Nếu không
thể tìm được ở database. Tiến hành sang bước 2

Bước 2: Tìm thuốc trên internet

Dùng lại tên ban đầu, chuẩn hoá theo rule khác

Tiến hành chạy tiếp thuật toán tìm kiếm như bình
thường
