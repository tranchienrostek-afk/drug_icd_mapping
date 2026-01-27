# Domain: Drugs Master

Dữ liệu chủ đề (Master Data) về thuốc, bao gồm thông tin hành chính, thành phần và chỉ định.

## 1. Bảng `drugs`
Bảng lưu trữ dữ liệu thuốc chính thức sau khi đã qua kiểm duyệt.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng (RowID) |
| `ten_thuoc` | TEXT | Tên thương mại của thuốc |
| `so_dang_ky` | TEXT | Số đăng ký lưu hành (SDK) |
| `hoat_chat` | TEXT | Tên hoạt chất chính |
| `cong_ty_san_xuat` | TEXT | Công ty sản xuất |
| `chi_dinh` | TEXT | Công dụng và chỉ định điều trị |
| `tu_dong_nghia` | TEXT | Từ đồng nghĩa (hỗ trợ search) |
| `classification` | TEXT | Phân loại bổ sung (ETC/OTC/...) |
| `note` | TEXT | Ghi chú từ thẩm định viên |
| `is_verified` | INTEGER | Trạng thái xác minh (1=Verified) |
| `search_text` | TEXT | Trường tổng hợp cho FTS Search |
| `created_by` | TEXT | Người tạo |
| `created_at` | TIMESTAMP | Thời điểm tạo |
| `updated_by` | TEXT | Người cập nhật cuối cùng |
| `updated_at` | TIMESTAMP | Thời điểm cập nhật cuối |

## 2. Bảng `drug_staging`
Khu vực trung gian (Staging Area) lưu trữ dữ liệu thô từ Crawler, Import hoặc đóng góp từ cộng đồng trước khi được duyệt vào bảng chính.

| Cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | INTEGER | Khóa chính tự tăng |
| `ten_thuoc` | TEXT | Tên thuốc đề xuất |
| `so_dang_ky` | TEXT | SDK đề xuất |
| `hoat_chat` | TEXT | Hoạt chất |
| `cong_ty_san_xuat` | TEXT | Công ty SX |
| `chi_dinh` | TEXT | Chỉ định |
| `tu_dong_nghia` | TEXT | Từ đồng nghĩa |
| `search_text` | TEXT | Text tìm kiếm thô |
| `status` | TEXT | Trạng thái: `pending`, `approved`, `rejected` |
| `conflict_type` | TEXT | Loại xung đột phát hiện: `sdk` (trùng SDK), `name` (trùng tên) |
| `conflict_id` | INTEGER | ID của thuốc gốc trong bảng drugs (nếu conflict) |
| `classification` | TEXT | Phân loại |
| `note` | TEXT | Ghi chú |
| `created_by` | TEXT | Người submit |
| `created_at` | TIMESTAMP | Thời điểm submit |

## 3. Tìm kiếm (`drugs_fts`)
Bảng ảo (Virtual Table) sử dụng FTS5 để hỗ trợ tìm kiếm toàn văn tốc độ cao.
- **Cột index**: `ten_thuoc`, `hoat_chat`, `cong_ty_san_xuat`, `search_text`.
- **Cơ chế**: Dùng tokenizer để tách từ, hỗ trợ prefix search (`query*`).

## 4. Nguồn Dữ Liệu (Source Data) - `datacore_thuocbietduoc`
Thư mục: `C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\datacore_thuocbietduoc`

Lưu trữ dữ liệu thô và dữ liệu đã xử lý từ quá trình cào (crawling) trang `thuocbietduoc.com.vn`.

### 4.1. Dataset Chính: `dulieu_thuoc_playwright.csv`
Đây là file tổng hợp đã qua xử lý sơ bộ, chứa danh sách đầy đủ các thuốc đã cào được.
- **Kích thước**: ~3.7 MB
- **Số lượng bản ghi**: ~20,000+ dòng (ước tính từ số trang start 1829 -> 3424 trong script)

| Cột (Header) | Mô tả | Ví dụ |
| :--- | :--- | :--- |
| `so_dang_ky` | Số đăng ký thuốc (SDK) | `VN-10300-05` |
| `ten_thuoc` | Tên thương mại của thuốc | `Zithromax 200mg/5ml` |
| `hoat_chat` | Thành phần hoạt chất | `Azithromycin` |
| `noi_dung_dieu_tri` | Nội dung chỉ định chi tiết | `Chỉ định Azithromycin được chỉ định...` |
| `ma_icd` | Mã bệnh ICD (gắn kết sau) | (Trống hoặc dữ liệu sau xử lý) |
| `trang_thai_xac_nhan` | Trạng thái kiểm duyệt | `Pending` |
| `dang_bao_che` | Dạng bào chế của thuốc | `Bột pha hỗn dịch uống` |
| `danh_muc` | Phân loại nhóm thuốc | (Thường trống trong raw) |
| `ham_luong` | Hàm lượng hoạt chất | (Thường trống trong raw) |
| `url_nguon` | Link gốc trên thuocbietduoc | `https://thuocbietduoc.com.vn/...` |

### 4.2. Raw Parts: `ketqua_thuoc_part_*.csv`
Các file chứa kết quả cào thô theo từng phiên chạy (từng part), ví dụ `ketqua_thuoc_part_20260106_190030.csv`.
- **Cấu trúc**: Tương tự dataset chính nhưng có thể thiếu các cột `ma_icd`, `trang_thai_xac_nhan`.

### 4.3. Scraper: `scrapper_data_drugs.py`
Script Python sử dụng `playwright` để cào dữ liệu.
- **Target**: `https://thuocbietduoc.com.vn/thuoc/drgsearch.aspx`
- **Logic**: Duyệt qua các trang (Pagination), vào từng link thuốc đẻ lấy chi tiết.
- **Fields Extracted**: SDK, Tên, Hoạt chất, Chỉ định, Dạng bào chế, Nhóm thuốc, Hàm lượng, URL.

