
---

# 📄 TÀI LIỆU KỸ THUẬT: QUY ĐỊNH LOGIC MAPPING (CATEGORY - VALIDITY - ROLE)

## 1. ❌ BÁO CÁO SỰ CỐ (BUG REPORT)

### Mô tả lỗi

Hệ thống đang thực hiện mapping sai lệch giữa `role` và `category`. Cụ thể, khi xác định sản phẩm là "Thiết bị y tế" (`medical equipment`), hệ thống lại gán nhầm category là "Thuốc" (`drug`).

### Request (Mẫu tái hiện lỗi)

**Bash**

```
curl -X 'POST' \
  'http://10.14.190.28:8000/api/v1/consult_integrated' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "diagnoses": [{"code": "J00", "name": "Viêm mũi họng cấp", "type": "MAIN"}],
  "items": [{"id": "916b023e...", "name": "natriclorid srk saltmax 0 45g 50ml x 100ml"}],
  "request_id": "BT/24594",
  "symptom": "Viêm đường hô hấp"
}'
```

### Output Sai (Hiện tại)

**JSON**

```
{
  "results": [
    {
      "category": "drug",          // ❌ SAI: Thiết bị y tế không thể là drug
      "validity": "valid",         // ❌ SAI: Thiết bị y tế thì validity phải trống
      "role": "medical equipment",
      "explanation": "Expert Verified: Classified as 'medical equipment'..."
    }
  ]
}
```

**Nguyên tắc vi phạm:** `role: medical equipment` → `category` PHẢI là `nodrug`.

---

## 2. ✅ QUY TẮC MAPPING TUYỆT ĐỐI (BUSINESS RULES)

### Cấu trúc phân cấp dữ liệu

Sử dụng cấu trúc cây dưới đây làm chuẩn:

**Plaintext**

```
Sản phẩm
├── category: drug
│   ├── validity: invalid → (Bắt buộc KHÔNG có role)
│   └── validity: valid
│       ├── role: main drug
│       └── role: secondary drug
│
└── category: nodrug
    ├── validity: "" (Chuỗi rỗng)
    └── role:
        ├── supplement
        ├── cosmeceuticals
        └── medical equipment
```

### Các quy tắc Logic (BẮT BUỘC)

**Nhóm 1: Logic xác định theo Role (Ưu tiên cao nhất)**

* Nếu Role là `main drug` hoặc `secondary drug` → Bắt buộc map về: **Category `drug`** +  **Validity `valid`** .
* Nếu Role là `supplement`, `cosmeceuticals`, hoặc `medical equipment` → Bắt buộc map về: **Category `nodrug`** +  **Validity `""` (trống)** .
* Nếu Role không tồn tại (null) → Map về: **Category `drug`** +  **Validity `invalid`** .

**Nhóm 2: Các tổ hợp Hợp lệ (Whitelist)**

Chỉ chấp nhận các output JSON có dạng sau:

1. `{"category": "drug", "validity": "invalid"}` (Không có role)
2. `{"category": "drug", "validity": "valid", "role": "main drug"}`
3. `{"category": "drug", "validity": "valid", "role": "secondary drug"}`
4. `{"category": "nodrug", "validity": "", "role": "supplement"}`
5. `{"category": "nodrug", "validity": "", "role": "cosmeceuticals"}`
6. `{"category": "nodrug", "validity": "", "role": "medical equipment"}`

**Nhóm 3: Các tổ hợp CẤM (Blacklist - Cần chặn đứng)**

* ❌ `category: drug` đi với `role: medical equipment`.
* ❌ `category: drug` đi với `role: supplement` hoặc `cosmeceuticals`.
* ❌ `category: nodrug` đi với `role: main drug` hoặc `secondary drug`.
* ❌ `category: nodrug` đi với `validity: valid` hoặc `invalid`.
* ❌ `category: drug` + `validity: invalid` mà lại có `role`.

---

## 3. 🔧 GIẢI PHÁP KỸ THUẬT (IMPLEMENTATION)

**File tham chiếu định nghĩa gốc:**

`C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent\logs_to_database\group_definitions.md`

### A. Code Validation (Thêm vào logic kiểm tra)

**Python**

```
def validate_mapping(category, validity, role):
    """
    Kiểm tra tính hợp lệ của mapping. Raise error nếu vi phạm.
    """
    # Rule 1: Các role thuộc nhóm NODRUG
    if role in ["supplement", "cosmeceuticals", "medical equipment"]:
        assert category == "nodrug", f"Lỗi logic: Role '{role}' phải có category='nodrug'"
        assert validity == "", f"Lỗi logic: Role '{role}' phải có validity trống"
  
    # Rule 2: Các role thuộc nhóm DRUG
    if role in ["main drug", "secondary drug"]:
        assert category == "drug", f"Lỗi logic: Role '{role}' phải có category='drug'"
        assert validity == "valid", f"Lỗi logic: Role '{role}' phải có validity='valid'"
  
    # Rule 3: Drug Invalid (Không dùng để điều trị)
    if category == "drug" and validity == "invalid":
        assert role is None or role == "", "Lỗi logic: Drug invalid không được phép có role"
  
    return True
```

### B. Code Auto-Correction (Tự động sửa lỗi)

Logic này dùng để chuẩn hóa dữ liệu đầu ra từ AI hoặc Feedback của TĐV.

**Python**

```
def auto_correct_mapping(category, validity, role):
    """
    Tự động sửa mapping category/validity dựa trên role (Role là nguồn sự thật).
    """
    # Ưu tiên 1: Role thuộc nhóm NODRUG -> Ép về nodrug
    if role in ["supplement", "cosmeceuticals", "medical equipment"]:
        return "nodrug", "", role
  
    # Ưu tiên 2: Role thuộc nhóm DRUG -> Ép về drug/valid
    if role in ["main drug", "secondary drug"]:
        return "drug", "valid", role
  
    # Ưu tiên 3: Nếu không có role và là drug -> Ép về invalid
    if category == "drug":
        return "drug", validity or "invalid", None
  
    # Default: Trả về nguyên gốc
    return category, validity, role
```

---

## 4. 🤖 CẬP NHẬT SYSTEM PROMPT CHO AI

Copy đoạn dưới đây vào System Prompt để AI nắm được logic xử lý:

**Markdown**

```
## MAPPING RULES - TUYỆT ĐỐI TUÂN THỦ

Bạn sẽ nhận được kết quả từ 2 nguồn: (1) AI classification và (2) Expert verification (Thẩm định viên - TĐV).

### Nguyên tắc ưu tiên xử lý:
1.  **Expert verification > AI classification**.
2.  Nếu TĐV không feedback → AI classification được coi là chính xác.
3.  Nếu nhiều TĐV có feedback khác nhau → suy luận để chọn kết quả tốt nhất.

### Quy tắc mapping BẮT BUỘC (Logic):
* **Trường hợp là THUỐC (Drug):**
    * Nếu Invalid: `category: drug` + `validity: invalid` (Không có role).
    * Nếu Valid (Chính): `category: drug` + `validity: valid` + `role: main drug`.
    * Nếu Valid (Phụ): `category: drug` + `validity: valid` + `role: secondary drug`.

* **Trường hợp KHÔNG PHẢI THUỐC (Nodrug):**
    * Thực phẩm chức năng: `category: nodrug` + `validity: ""` + `role: supplement`.
    * Dược mỹ phẩm: `category: nodrug` + `validity: ""` + `role: cosmeceuticals`.
    * Thiết bị y tế: `category: nodrug` + `validity: ""` + `role: medical equipment`.

### Validation Workflow (Quy trình tự kiểm tra):
1.  Nhận kết quả.
2.  Lấy `role` làm chuẩn.
3.  Tự động sửa `category` và `validity` tương ứng với `role`.
4.  Đảm bảo không vi phạm các tổ hợp cấm.
```

---

## 5. 📋 CHECKLIST KIỂM TRA DÀNH CHO DEV

Các bạn vui lòng tích vào từng mục sau khi đã hoàn thành code và trước khi merge:

* [ ] **Logic Code:** Đã implement hàm `auto_correct_mapping` để tự động sửa `category` thành `nodrug` nếu `role` là `medical equipment/supplement/cosmeceuticals`.
* [ ] **Logic Code:** Đã đảm bảo nếu `category` là `nodrug` thì trường `validity` bắt buộc phải là chuỗi rỗng `""`.
* [ ] **Logic Code:** Đã xử lý trường hợp `category: drug` + `validity: invalid` thì `role` phải bằng `null`.
* [ ] **Prompting:** Đã cập nhật System Prompt của AI với các quy tắc mapping mới.
* [ ] **Testing:** Đã chạy thử lại request mẫu (natriclorid srk saltmax) và ra kết quả đúng là `category: nodrug`.
* [ ] **Review:** Đảm bảo không tồn tại bất kỳ tổ hợp cấm nào (ví dụ: `drug` + `medical equipment`) trong database hoặc output log.

---

## 6. 📝 MẪU OUTPUT ĐÚNG (REFERENCE)

**Ví dụ 1: Thiết bị y tế (Medical Equipment)**

**JSON**

```
{
  "category": "nodrug",
  "validity": "",
  "role": "medical equipment"
}
```

**Ví dụ 2: Thuốc chính (Main Drug)**

**JSON**

```
{
  "category": "drug",
  "validity": "valid",
  "role": "main drug"
}
```

**Ví dụ 3: Thuốc không phù hợp (Invalid Drug)**

**JSON**

```
{
  "category": "drug",
  "validity": "invalid"
}
```


* *
