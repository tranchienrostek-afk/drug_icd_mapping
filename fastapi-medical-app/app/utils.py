import re

UNIT = r'(mg|g|mcg|iu|ml|l)' # Expanded slightly for safety
DOSE = rf'\d+(?:\.\d+)?\s*{UNIT}'
SEP = r'\+|/|,|\band\b|\bva\b'

def normalize_name(name: str) -> str:
    name = re.sub(r'\([^)]*\)', '', name)  # bỏ ngoặc
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title()

def normalize_dose(dose: str) -> str:
    return re.sub(r'\s+', '', dose.lower())

def normalize_drug_name(text: str):
    """
    Chuẩn hóa tên thuốc phức hợp thành dạng chuẩn:
    "Hoạt chất A Liều A + Hoạt chất B Liều B"
    """
    if not text: return None
    
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)

    # 1. Tách liều theo thứ tự xuất hiện
    # Use finditer to correctly capture full match matching the DOSE pattern
    doses_iter = re.finditer(DOSE, text)
    doses = [normalize_dose(m.group(0)) for m in doses_iter]

    # 2. Xoá liều để lấy tên hoạt chất
    text_wo_dose = re.sub(DOSE, ' ', text)

    # 3. Tách hoạt chất theo separator
    raw_acts = re.split(SEP, text_wo_dose)

    actives = []
    for a in raw_acts:
        a = a.strip()
        # Clean special chars but keep letters/numbers (e.g. Vit B12)
        # a = re.sub(r'[^\w\s]', '', a) # Careful with this
        if len(a) >= 2 and re.search(r'[a-z]', a):
            actives.append(normalize_name(a))

    if not actives or not doses:
        return None

    # 4. Ghép 1-1 theo index
    components = []
    for i, act in enumerate(actives):
        if i < len(doses):
            components.append(f"{act} {doses[i]}")
        else:
            # If no dose for this active (e.g. combined pack?), just add active
             components.append(act)

    return " + ".join(components) if components else None

def normalize_text(text: str) -> str:
    """
    Hàm chuẩn hóa text chung cho hệ thống (đã tồn tại trước đó).
    Loại bỏ dấu, chuyển thường, xóa ký tự đặc biệt.
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'đ', 'd', text)
    # Giữ lại a-z, 0-9 và khoảng trắng
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()