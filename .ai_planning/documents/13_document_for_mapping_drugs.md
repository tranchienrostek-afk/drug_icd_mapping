# Hướng dẫn Kỹ thuật: API Mapping Thuốc (Claims vs Medicine)

Tài liệu này mô tả chi tiết về các biến đầu vào, đầu ra và logic xử lý của dịch vụ so khớp thuốc.

---

## 1. Thông tin chung
- **API Endpoint**: `POST /api/v1/mapping/match`
- **Mục tiêu**: So khớp danh sách thuốc khách hàng yêu cầu bồi thường (**Claims**) với danh sách thuốc khách hàng đã thực tế mua trên hóa đơn (**Medicine**).

---

## 2. Cấu trúc Dữ liệu Đầu vào (MatchingRequest)

API chấp nhận một JSON object với các trường sau:

| Trường | Kiểu dữ liệu | Ý nghĩa |
| :--- | :--- | :--- |
| `request_id` | `string` | ID duy nhất của yêu cầu (tùy chọn). |
| `claims` | `List[ClaimItem]` | Danh sách các thuốc cần thanh toán bồi thường. |
| `medicine` | `List[MedicineItem]` | Danh sách các thuốc có trên hóa đơn mua hàng. |
| `config` | `dict` | Cấu hình nâng cao (ví dụ: `ai_model`). |

### ClaimItem / MedicineItem
Cả hai danh sách đều sử dụng cấu trúc tương tự:
- `id`: ID của danh mục thuốc trong hệ thống.
- `service_name`: Tên thuốc/dịch vụ (Raw name).
- `amount`: Giá trị (số tiền) của thuốc.

---

## 3. Cấu trúc Dữ liệu Đầu ra (MatchingResponse)

Kết quả trả về bao gồm so khớp thành công và danh sách các bất thường (anomalies).

### 3.1. `results` (Danh sách các cặp đã khớp)
Chỉ chứa các cặp thuốc được coi là khớp (status != `no_match`).
- `claim_id`: ID của claim.
- `medicine_id`: ID của medicine tương ứng.
- `match_status`: Mức độ khớp (`matched`, `partially_matched`, `weak_match`).
- `confidence_score`: Điểm tin cậy (0.0 - 1.0).
- `evidence`: Bằng chứng so khớp (Text similarity, Method, AI reasoning).

### 3.2. `anomalies` (Các bất thường)
Đây là phần quan trọng để phát hiện sai lệch hoặc gian lận:
- **`claim_without_purchase`**: Danh sách Claims **không** tìm thấy thuốc tương ứng trong hóa đơn.
- **`purchase_without_claim`**: Danh sách Medicine đã mua nhưng **không** có trong yêu cầu bồi thường.

### 3.3. `summary` (Tổng hợp)
Thống kê nhanh số lượng items đã khớp, risk level (low/medium/high), và số lượng cần review thủ công.

---

## 4. Logic Xử lý & "Luật" So khớp

Hệ thống sử dụng quy trình 3 lớp để đảm bảo độ chính xác cao nhất:

### Lớp 1: Khớp chính xác (Deterministic Match)
- Kiểm tra theo tên đã chuẩn hóa (Normalization) và mã SDK (Số đăng ký) nếu có trong Database.

### Lớp 2: Khớp mờ (Fuzzy Match - Relaxed)
- Sử dụng thuật toán `rapidfuzz` với ngưỡng (threshold) **70%**.
- Cho phép khớp các tên thuốc có sai biệt nhỏ về chính tả, khoảng trắng hoặc ký tự đặc biệt.

### Lớp 3: Trí tuệ nhân tạo (AI Semantic Match)
- Nếu logic thông thường thất bại, AI (LLM) sẽ được gọi để phân tích ngữ nghĩa.
- **Xử lý từ đồng nghĩa (Synonyms)**: AI được huấn luyện để tự động hiểu các thuật ngữ tương đương mà không cần hardcode:
    - *Betadine suc hong* (Tiếng Việt) ↔ *Betadine Gargle* (Tiếng Anh).
    - *Syrup* ↔ *Siro*.
    - *Tab/Tablet* ↔ *Viên*.
- **Quy tắc nới lỏng**: Ưu tiên tính tương đương về hoạt chất và dạng bào chế để bảo vệ quyền lợi khách hàng (tin tưởng hơn, trừ khi có dấu hiệu gian lận rõ ràng).

---

## 5. Ý nghĩa Truyền tải (Business Impact)
1. **Tự động hóa**: Giảm 80-90% công sức review thủ công cho các hóa đơn thuốc.
2. **Minh bạch**: Cung cấp `evidence` và `reasoning` cho từng quyết định so khớp.
3. **Chống gian lận**: Mục `anomalies` chỉ ra chính xác những loại thuốc nào được yêu cầu bồi thường nhưng thực tế không có hóa đơn hợp lệ.
4. **Trải nghiệm khách hàng**: Nhận diện thông minh các từ đồng nghĩa Việt-Anh giúp giảm tỷ lệ từ chối bồi thường sai (false negative).
