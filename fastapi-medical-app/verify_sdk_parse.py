from app.service.web_crawler import parse_drug_info
import re

texts = [
    "Số đăng ký: VN-12345-12, Công ty: ABC",
    "SĐK: VD-6789-10, Thành phần: X",
    "Reg.No: GC-1122-33",
    "Đây là thuốc có số đăng ký VNA-4455-22",
    "QLD-9988-77"
]

print("START_TEST")
for t in texts:
    res = parse_drug_info(t)
    print(f"SDK_FOUND: {res.get('so_dang_ky')}")
print("END_TEST")
