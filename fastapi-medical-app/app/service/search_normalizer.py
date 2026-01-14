"""
Search Normalizer - Simplified version without Excel dependency.
Extracts only the drug name prefix, removing dosage, units, and special characters.
"""
import re

def normalize_drug_name(text: str) -> str:
    """
    Chuẩn hóa tên thuốc cho web search.
    Rules:
    1. Loại bỏ ký tự đặc biệt: -, (, ), [, ], /, \
    2. Loại bỏ số liều/dung tích: 200mg, 10ml, 500mg, etc.
    3. Loại bỏ các từ đơn vị: liều, xịt, viên, ống, ml, mg, g, mcg
    4. Giữ lại tên thuốc chính (thường là 1-2 từ đầu)
    """
    if not text:
        return ""
    
    original = text
    
    # 1. Xóa nội dung trong ngoặc
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # 2. Xóa dấu gạch ngang và ký tự đặc biệt
    text = re.sub(r'[-–—/\\]', ' ', text)
    
    # 3. Xóa số kèm đơn vị (200mg, 10ml, 500mcg, etc.)
    text = re.sub(r'\d+\s*(mg|ml|g|mcg|iu|ui|liều|viên|ống|xịt|gói|chai|lọ|hộp)\b', '', text, flags=re.IGNORECASE)
    
    # 4. Xóa các từ đơn vị đứng riêng
    text = re.sub(r'\b(liều|xịt|viên|ống|gói|chai|lọ|hộp|mg|ml|mcg)\b', '', text, flags=re.IGNORECASE)
    
    # 5. Xóa số đứng riêng (như "200", "10", "120")
    text = re.sub(r'\b\d+\b', '', text)
    
    # 6. Chuẩn hóa khoảng trắng
    text = ' '.join(text.split())
    
    # 7. Strip và trả về
    result = text.strip()
    
    # Log for debugging
    if result != original:
        print(f"[Normalizer] '{original}' -> '{result}'")
    
    return result if result else original.split()[0]  # Fallback to first word


if __name__ == "__main__":
    test_cases = [
        "Ludox - 200mg",
        "Berodual 200 liều (xịt) - 10ml",
        "Symbicort 120 liều",
        "Panadol Extra 500mg",
        "Vitamin C 1000mg/10ml",
        "Thuốc ho Bảo Thanh (Chai 125ml)",
    ]
    
    print("-" * 50)
    for t in test_cases:
        cleaned = normalize_drug_name(t)
        print(f"Gốc   : '{t}'")
        print(f"Clean : '{cleaned}'")
        print("-" * 50)
