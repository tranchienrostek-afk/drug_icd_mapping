Mỗi ngày hệ thống chủ sẽ bắn logs trong ngày hôm trước về service này.

Tôi cần xây API mở ra để hệ thống máy chủ lớn của công ty bắn logs về

1. Sau ghi nhận được logs tôi tiến hành lưu logs lại trước
2. Sau khi đã lưu được logs về rồi tôi tiến hành làm sạch dữ liệu. Dữ liệu làm sạch cũng được lưu vào một chỗ.
3. Sau khi làm sạch được rồi tôi tiến hành bóc tách để lưu dữ liệu vào các bảng đã thiết kế cho bài toán drugs, icd này.

Mục tiêu: Khách hàng tương tác rất nhiều với hệ thống, các bạn thẩm định viên cũng sửa đổi tên thuốc, tên bệnh và điều chỉnh rất nhiều những dữ liệu khách hàng gửi. Tôi thấy rằng dữ liệu này hoàn toàn có thể làm giàu thêm chi thức trong hệ thống thuốc và bệnh hiện tại này của tôi.

Về sau gặp trường hợp đó thì database có rồi, được làm giàu rồi thì không cần phải tốn tiền search internet nữa.

Tôi sẽ cung cấp logs mẫu cho phần phân loại thuốc tại địa chỉ: C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\app\logs\logs_api\data-1768208166532.csv

Hiện tôi chia sẻ logs mẫu cũng chưa rõ được cấu trúc.

Tôi cần trao đổi với Việt, bạn dev của hệ thống để 2 bên trao đổi xem cần lấy những trường thông tin nào cho có ý nghĩa. Nhưng để trao đổi với bạn ấy cho hiệu quả tôi cần bạn

C:\Users\Admin\Desktop\drug_icd_mapping\.multi agents\01_business_analyst.md

và C:\Users\Admin\Desktop\drug_icd_mapping\.multi agents\02_ai_scientist.md

Hoàn thiện đầy đủ bản kế hoạch này

Cũng lên trước những trường dữ liệu cần có trong logs để có thể gửi Việt cũng được, chuẩn bị thôi chứ cũng chưa biết bạn Việt có gửi được không

Mình cứ chủ động lên kế hoạch trước

Sau đó có gì thì update thông tin tiếp

Cung cấp thêm thông tin cho bạn, bạn có thể lưu trữ thông tin vô cùng quan trọng này mà tôi bắt đầu cung cấp:

Hệ thống bên tôi là hệ thống thẩm định bảo hiểm lớn

Tất cả hồ sơ của khách hàng, hồ sơ claim, các gói quyền lợi... đều được vào web bên tôi.

Hiện service tôi và bạn đang triển khai chỉ có nhiệm vụ lưu trữ dữ liệu về bệnh và thuốc. Hỗ trợ mapping và ra quyết định thông minh liên quan đến bệnh và thuốc.

Còn toàn bộ sản phẩm thì có nhiều bên đang build service khác lắm.

Trong đó thì việc lịch sử từ xưa đến giờ về việc thẩm định ấy, dữ liệu lưu vào logs nhiều, từ việc thuốc này thuộc nhóm nào, thuốc này có được bảo hiểm không, các bệnh lý như nào, bệnh nào dược loại trừ.

tôi nghĩ là những dữ liệu quý giá này nên được service của tôi lưu lại và khai phá chúng.

Còn rất nhiều việc, nhưng tôi tin chúng ta có thể chia nhỏ task và chinh phục được nó.
