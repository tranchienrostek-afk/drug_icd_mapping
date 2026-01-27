Phát triển giải pháp

đối với API /api/v1/consult_integrated

Khi thẩm định viên feedback là "" hoặc null thì suy luận căn cứ vào kết quả AI trả ra 

Ví dụ

**AI phân loại là: drug, valid**

Trong khi đó TDV là con người, vì lỗi gì đó hay mặc định đồng ý với kết quả chính xác của AI mà để là null

Khi đó người dùng gọi API /api/v1/consult_integrated

ưu tiên kết quả của thẩm định viên

Nên vẫn gọi ý thuốc này thuộc nhóm null (vì nó đã quá tin thẩm định viên)

Hãy phát triển giải pháp để ổn định và chính xác hơn

Nhớ viết unittest.
