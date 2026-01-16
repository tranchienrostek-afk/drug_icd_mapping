
Tôi trao đổi lại cách chuyển file csv này vào bảng database
nhé

Có chút xử lý chưa được thoả mãn tôi

Thông báo:

Cách xử lý từng cột trong file CSV

Đối với cột:

Phân loại (ở dạng 1 danh sách đó, vì một thuốc hệ thống có
thể phân thành nhiều loại)

Feedback(ở dạng 1 danh sách đó, vì một thuốc hệ thống có thể
phân thành nhiều loại)

Khi chuyển vào database sẽ chỉ để duy nhất 1 cột là:

treatment_type

Tức là cột phân loại và Feedback được mapping về lại thành
treatment_type

Kiểu string ghép vào đại loại như sau:

AI:  {drug, main}, TDV:
{drug}

Cột: **Lý do kê đơn**

Thêm đi để lưu trữ lại lý do AI kê đơn, giờ chưa dừng nhưng
cứ kê lại

Đối với cột

Cách dùng

SL

ð
Tạm thời không đưa vào bảng

Đối với cột: Tên thuốc

Sẽ được lưu trữ dưới dạng 2 cột

Cột 1 là

**drug_name_norm:
Chuẩn hoá tên thuốc**

**drug_name:
Tên thuốc gốc lấy nguyên từ csv đưa vào đây**

**Đối với
cột: **

**Mã ICD
(Chính)          **

**Bệnh
phụ**

**Đây là
một phần khó, vì một người bệnh sẽ có nhiều hơn 1 loại bệnh đi khám**

**Hệ thống
được mapping như sau**

**Ví dụ**

**Mã ICD
(Chính): **J00 - Viêm mũi họng cấp [cảm thường]

**Hệ thống
cần bóc**

**Mã icd
là: j00**

**Tên bệnh
là: **Viêm mũi họng cấp [cảm thường]

Và tạo
ra các cột cho bệnh chính gồm

**disease_name_norm:
Tên bệnh chính chuẩn hoá**

**disease_name:
Tên bệnh chính gốc**

**disease_icd:
Mã icd của bệnh chính**

**disease_ref_id:
Liên hệ vào bảng bệnh với bệnh chính, không biết có tìm được không nhưng cứ tạo
mối liên hệ ở đây, xem mã icd này ở bảng bệnh đang có id bao nhiêu**

**Cột bệnh
phụ cũng cần tạo cột vào bảng**

**Bệnh
phụ: B97.4 - Vi rút hợp bào đường hô hấp**

**Hệ thống
cần bóc: mã icd bệnh phụ**

**Tên gốc
bệnh phụ**

**Tên đã
chuẩn hoá của bệnh phụ**

**disease_ref_id
=> Dành cho bệnh phụ, xem mã icd này ở bảng bệnh đang có id bao nhiêu**

**Tên cột: Chẩn đoán ra viện**

**Nên tạo
cột ở database: **symptom và giữ nguyên nội dung

**Cột: **
