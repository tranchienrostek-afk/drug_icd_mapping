"""
Normalizer Module - Chuẩn hóa tên thuốc cho matching
=====================================================
Standalone implementation, không phụ thuộc API bên ngoài.
"""

import re
import unicodedata
from typing import Optional


def normalize_for_matching(text: str) -> str:
    """
    Chuẩn hóa tên thuốc để fuzzy match trong DB.
    
    Quy tắc:
    - Lowercase
    - Bỏ dấu tiếng Việt (convert to ASCII)
    - Giữ lại: a-z, 0-9, space, -, +, %, .
    - Bỏ leading zeros (05ml -> 5ml)
    
    Args:
        text: Tên thuốc thô (raw drug name)
        
    Returns:
        Tên thuốc đã chuẩn hóa
    """
    if not text:
        return ""

    text = text.lower()
    
    # Bỏ dấu tiếng Việt
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = text.replace('đ', 'd')
    text = text.replace('Đ', 'd')

    # Thay separators thành space
    text = text.replace("/", " ")
    text = re.sub(r'[\(\)\[\]]', ' ', text)

    # Chỉ giữ ký tự hợp lệ: a-z, 0-9, space, -, +, %, .
    text = re.sub(r'[^a-z0-9\s\-\+\%\.]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Bỏ leading zeros: 05ml -> 5ml, 03 -> 3
    def strip_leading_zeros(match):
        num = match.group(1).lstrip('0') or '0'  # Giữ ít nhất 1 số 0
        suffix = match.group(2) or ''
        return num + suffix
    
    text = re.sub(
        r'\b0+(\d+)(ml|mg|mcg|g|iu|ui|l|%)?', 
        strip_leading_zeros, 
        text, 
        flags=re.IGNORECASE
    )
    
    return text


def normalize_drug_name(text: str) -> Optional[str]:
    """
    Chuẩn hóa tên thuốc phức hợp thành dạng chuẩn:
    "Hoạt chất A Liều A + Hoạt chất B Liều B"
    
    Ví dụ:
    - "Amoxicillin 500mg/Clavulanic 125mg" -> "Amoxicillin 500mg + Clavulanic 125mg"
    """
    if not text:
        return None
    
    UNIT = r'(mg|g|mcg|iu|ml|l)'
    DOSE = rf'\d+(?:\.\d+)?\s*{UNIT}'
    SEP = r'\+|/|,|\band\b|\bva\b'
    
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)

    # Tách liều theo thứ tự xuất hiện
    doses_iter = re.finditer(DOSE, text)
    doses = [re.sub(r'\s+', '', m.group(0)) for m in doses_iter]

    # Xoá liều để lấy tên hoạt chất
    text_wo_dose = re.sub(DOSE, ' ', text)

    # Tách hoạt chất theo separator
    raw_acts = re.split(SEP, text_wo_dose)

    actives = []
    for a in raw_acts:
        a = a.strip()
        if len(a) >= 2 and re.search(r'[a-z]', a):
            # Title case
            actives.append(a.strip().title())

    if not actives or not doses:
        return None

    # Ghép 1-1 theo index
    components = []
    for i, act in enumerate(actives):
        if i < len(doses):
            components.append(f"{act} {doses[i]}")
        else:
            components.append(act)

    return " + ".join(components) if components else None


def extract_keywords(text: str) -> list:
    """
    Trích xuất keywords từ tên thuốc để search.
    
    Loại bỏ noise words như: hộp, chai, vỉ, viên, etc.
    """
    if not text:
        return []
    
    noise_words = {
        'hộp', 'hop', 'box', 'chai', 'bottle', 'vỉ', 'vi', 
        'viên', 'vien', 'tabs', 'cap', 'capsule', 'tablet',
        'ống', 'ong', 'tube', 'gói', 'goi', 'sachet'
    }
    
    normalized = normalize_for_matching(text)
    words = normalized.split()
    
    # Filter noise và từ quá ngắn
    keywords = [w for w in words if w not in noise_words and len(w) >= 2]
    
    return keywords
