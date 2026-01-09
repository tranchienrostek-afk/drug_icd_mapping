import re
import unicodedata

def normalize_drug_name_draft(text: str) -> str:
    """
    Hàm chuẩn hóa tên thuốc (Draft Version).
    Mục tiêu:
    - Chuyển về chữ thường.
    - Xử lý tiếng Việt có dấu (giữ nguyên hoặc chuyển về không dấu tùy ý, ở đây ưu tiên chuyển về dạng clean ASCII để search tối ưu).
    - Giữ lại các ký tự quan trọng cho thuốc: chữ cái, số, dấu gạch nối (-), dấu cộng (+), dấu phần trăm (%), dấu x (x).
    - Loại bỏ các ký tự đặc biệt gây nhiễu (dấu ngoặc, dấu chấm thừa...).
    - Chuẩn hóa khoảng trắng.

    Input: "Berodual 200 liều (xịt) - 10ml"
    Output: "berodual 200 lieu xit 10ml"
    """
    if not text:
        return ""

    # 1. Chuyển về chữ thường
    text = text.lower()

    # 2. Xử lý tiếng Việt: Chuyển đổi các ký tự unicode dựng sẵn/tổ hợp về dạng cơ bản
    # Cách này giúp 'liều' -> 'lieu', 'xịt' -> 'xit' thay vì bị lỗi font
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])

    # 3. Thay thế một số ký tự đặc biệt thường gặp trong thuốc
    # Dấu / (ví dụ: mg/ml) -> mg ml
    text = text.replace("/", " ")
    # Dấu ( ) [ ] -> khoảng trắng
    text = re.sub(r'[\(\)\[\]]', ' ', text)

    # 4. Filter: Chỉ giữ lại a-z, 0-9, và các ký tự đặc biệt cho phép (- + % .)
    # Lưu ý: 'đ' sau khi qua bước 2 đã thành 'd'
    # Pattern: Giữ lại chữ, số, khoảng trắng, gạch ngang, cộng, phần trăm, chấm
    text = re.sub(r'[^a-z0-9\s\-\+\%\.]', ' ', text)

    # 5. Xử lý khoảng trắng thừa (nhiều space -> 1 space, trim 2 đầu)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def test_normalization():
    test_cases = [
        "Berodual 200 liều (xịt) - 10ml",
        "Panadol Extra",
        "Augmentin 1g",
        "Efferalgan 500mg",
        "Zinnat 500mg",
        "Ludox - 200mg",
        "Vitamin C 500mg + Kẽm",
        "Oresol 245 (cam) 4,1g",
        "Dung dịch tiêm 0.9%"
    ]

    print(f"{'ORIGINAL':<40} | {'NORMALIZED':<40}")
    print("-" * 85)
    for case in test_cases:
        norm = normalize_drug_name_draft(case)
        print(f"{case:<40} | {norm:<40}")

if __name__ == "__main__":
    test_normalization()
