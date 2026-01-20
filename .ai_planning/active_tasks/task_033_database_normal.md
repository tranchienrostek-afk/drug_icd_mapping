Cách để kết nối bảng knowledge_base và bảng diseases:

disease_ref_id # Bệnh chính liên kết vào bảng diseases thông
qua disease_icd của bảng kb và `icd_code` của bảng diseases

secondary_disease_ref_id # Bệnh phụ liên kết vào bảng diseases
thông qua secondary_disease_icd của bảng kb và `icd_code` của bảng diseases

Điều quan trọng của bệnh chính và bệnh phụ là phải tách được
mã ICD từ tên thuốc ra.

Cách kết nối knowledge_base và bảng `drugs`

drug_ref_id

Không dễ dàng như kết nối KB với bệnh, vì 2 bảng này đều có
thể tìm với nhau qua mã ICD.

Hiện bảng drugs khi một thuốc đặc trưng và uy tín thì sẽ có
số đăng ký chính là cột có tên: so_dang_ky

Nhưng ở bảng knowledge_base thì các loại thuốc không được
truyền số đăng ký.

Do đó chúng ta cần sử dụng mapping theo fuzzy, bm25,
embedding của giá trị bảng drug_name, drug_name_norm (đã từng xây dưungj trước đây
cho bài toán api: /api/v1/drugs/identify
bỏ qua phần search web và dùng AI thôi) các thể loại để xem tên thuốc ở
KB mapping được với tên thuốc nào trong drugs.

Nếu đạt (vượt qua ngưỡng tin cậy) thì nhận được số đăng ký và
cố gắng ghép nối drug_ref_id. Còn nếu không tìm được thì tạm để drug_ref_id là
null thôi.

Sau đó khi import cũng báo cáo kết quả import luôn

Bao nhiêu thuốc mapping được với thuốc của cơ sở dữ liệu

Bao nhiêu bệnh mapping được

Để mỗi lần import còn biết tình hình thế nào.

Với trường hợp

Thuốc và bệnh đã từng xuất hiện ở bảng knowledge_base trước đây
thì cứ thêm vào nếu về sau xuất hiện. Điều chỉnh mã ID là được vì chúng tôi không
muốn mất dữ liệu. Sau tổng hợp có thể dễ dàng biết được các cặp ấy đã từng xuất
hiện bao nhiêu lần.
