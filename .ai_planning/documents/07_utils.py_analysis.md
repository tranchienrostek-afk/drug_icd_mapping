# Phân Tích `app/utils.py`

Module `app/utils.py` chứa các hàm tiện ích dùng chung (Utility Functions), chủ yếu tập trung vào việc **chuẩn hóa văn bản (Text Normalization)**. Đây là thành phần cực kỳ quan trọng giúp hệ thống tìm kiếm và so khớp dữ liệu chính xác.

## 1. Chuẩn Hóa Để Khớp Database (`normalize_for_matching`)

Hàm `normalize_for_matching(text)` được thiết kế để phục vụ việc **Fuzzy Matching** (so khớp mờ) trong cơ sở dữ liệu nội bộ.

- **Mục tiêu**: Loại bỏ tối đa nhiễu để đưa về dạng ASCII thuần túy đơn giản nhất.
- **Logic**:
    1.  **Lowercase**: Chuyển về chữ thường.
    2.  **Xóa Dấu Tiếng Việt**: "Panadol đỏ" -> "panadol do".
    3.  **Thay Thế Ký Tự**: Chuyển `/` thành khoảng trắng, loại bỏ ngoặc `()`, `[]`.
    4.  **Whitelist Ký Tự**: Chỉ giữ lại `a-z`, `0-9`, khoảng trắng, `-`, `+`, `%`, `.`. Các ký tự khác (như `@`, `#`, `&`) sẽ bị xóa.
    5.  **Trim**: Loại bỏ khoảng trắng thừa.

> [!NOTE]
> Hàm này chấp nhận mất mát thông tin (ví dụ dấu tiếng Việt) để tăng khả năng khớp chuỗi khi người dùng gõ không dấu hoặc sai chính tả.

## 2. Chuẩn Hóa Để Tìm Kiếm Web (`normalize_for_search`)

Hàm `normalize_for_search(text)` dùng khi gửi từ khóa lên Google hoặc các Search Engine khác.

- **Mục tiêu**: An toàn và tuân thủ chặt chẽ danh sách ký tự cho phép (Allowed Charset).
- **Cơ chế**:
    - Load whitelist từ file `app/static/allowed_charset.xlsx`.
    - Duyệt từng ký tự của chuỗi đầu vào.
    - **Dừng ngay lập tức (Break)** tại ký tự không hợp lệ đầu tiên.
    - -> **Lý do**: Để tránh gửi các truy vấn rác hoặc query injection nguy hiểm lên Bot Search Agent.

## 3. Chuẩn Hóa Tên Thuốc Phức Hợp (`normalize_drug_name`)

Hàm `normalize_drug_name(text)` xử lý các chuỗi tên thuốc chứa cả hoạt chất và liều lượng, thường gặp trong dữ liệu thô.

- **Input**: "Hoạt chất A Liều A + Hoạt chất B Liều B" (Ví dụ: `Amoxicillin 500mg + Clavulanic 125mg`).
- **Logic**:
    1.  **Tách Liều (Dose)**: Dùng Regex tìm tất cả các cụm liều lượng (số + đơn vị mg/ml/...).
    2.  **Tách Hoạt Chất**: Xóa liều khỏi chuỗi, sau đó tách phần còn lại bằng dấu phân cách (`,`, `+`, `/`).
    3.  **Ghép Cặp (Re-combine)**: Ghép hoạt chất thứ $i$ với liều lượng thứ $i$ theo thứ tự xuất hiện.
- **Output**: Chuỗi chuẩn hóa dạng `Hoạt chất1 Liều1 + Hoạt chất2 Liều2`.


---
Các hàm này đảm bảo tính nhất quán của dữ liệu khi đi từ Input -> Xử lý (Utils) -> Database.

## Tại Sao Tách Code sang `utils.py`?

Việc tách các hàm này ra file riêng thay vì để trong `service` tuân theo nguyên tắc **Separation of Concerns** (Phân tách mối quan tâm) và mang lại các lợi ích sau:

### 1. Hàm Thuần Khiết (Pure Functions) vs Logic Nghiệp Vụ
- **`utils.py`**: Chứa các hàm độc lập, đầu ra chỉ phụ thuộc vào đầu vào (như `normalize_text`). Chúng không quan tâm đến database hay trạng thái hệ thống. Giống như một cái "tuốc nơ vít", ai dùng cũng được.
- **`service`**: Chứa logic nghiệp vụ (Business Logic), thường xuyên phải gọi Database, API bên ngoài.

### 2. Tránh Phụ Thuộc Vòng (Circular Imports)
- `Service` thường import `Model`.
- `Model` đôi khi cần validator chuẩn hóa dữ liệu đễu cần gọi lại hàm chuẩn hóa.
- Nếu để hàm chuẩn hóa trong `Service` -> `Service` import `Model` -> `Model` import `Service` => **Lỗi Circular Import**.
- **Giải pháp**: Đẩy ra `utils.py` để cả hai cùng import.

### 3. Dễ Dàng Kiểm Thử (Unit Testing)
- Test `utils` rất dễ vì không cần giả lập (mock) Database.
