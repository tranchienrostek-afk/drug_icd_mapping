import re
import unicodedata
import os
import openpyxl

UNIT = r'(mg|g|mcg|iu|ml|l)' # Expanded slightly for safety
DOSE = rf'\d+(?:\.\d+)?\s*{UNIT}'
SEP = r'\+|/|,|\band\b|\bva\b'

# Path configuration
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Adjusted path for core/utils.py (up one more level?)
# APP_DIR is now app/core/.. -> app/
# In original utils.py (app/utils.py), APP_DIR = app/
# In app/core/utils.py, abspath is app/core/utils.py. dirname is app/core. dirname(dirname) is app/
# So same logic works if we add one more dirname call or adjust relative path?
# Let's check original: APP_DIR = os.path.dirname(os.path.abspath(__file__)) -> app/
# New: APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) -> app/
# STATIC_DIR = os.path.join(APP_DIR, "static") -> app/static. Correct.

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
    Hiện tại redirect về normalize_for_matching (cho DB fuzzy match).
    """
    return normalize_for_matching(text)

# --- NEW NORMALIZATION LOGIC ---

# Path configuration re-evaluation
# Original: APP_DIR = os.path.dirname(os.path.abspath(__file__)) -> app/
# New location: app/core/utils.py. 
# os.path.abspath(__file__) -> .../app/core/utils.py
# os.path.dirname(...) -> .../app/core
# os.path.dirname(os.path.dirname(...)) -> .../app
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(APP_DIR, "static")
ALLOWED_CHARS_FILE = os.path.join(STATIC_DIR, "allowed_charset.xlsx")
_ALLOWED_CHARS = set()

def load_allowed_chars():
    """Load allowed characters for Web Search Normalizer from Excel"""
    global _ALLOWED_CHARS
    if _ALLOWED_CHARS:
        return
        
    if not os.path.exists(ALLOWED_CHARS_FILE):
        print(f"Warning: Allowed chars file not found at {ALLOWED_CHARS_FILE}")
        return

    try:
        wb = openpyxl.load_workbook(ALLOWED_CHARS_FILE, read_only=True)
        ws = wb.active
        for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
            val = row[0]
            if val is not None:
                _ALLOWED_CHARS.add(str(val))
    except Exception as e:
        print(f"Error loading allowed chars: {e}")

# Pre-load if possible (or lazy load)
# load_allowed_chars()

def normalize_for_matching(text: str) -> str:
    """
    [STEP 1] Chuẩn hóa tên thuốc cho bài toán fuzzy map (DB).
    Follows: knowledge for agent/db_match_normalizer_rules.py
    - Lowercase
    - Remove Vietnamese accents (to clean ASCII)
    - Keep: a-z, 0-9, space, -, +, %, .
    - Remove others
    """
    if not text:
        return ""

    # 1. Lowercase
    text = text.lower()

    # 2. Handle Vietnamese accents
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = text.replace('đ', 'd')

    # 3. Replace common separators
    text = text.replace("/", " ")
    text = re.sub(r'[\(\)\[\]]', ' ', text)

    # 4. Filter allowed chars
    # Allow: a-z, 0-9, space, -, +, %, .
    text = re.sub(r'[^a-z0-9\s\-\+\%\.]', ' ', text)

    # 5. Trim spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def normalize_for_search(text: str) -> str:
    """
    [STEP 2] Chuẩn hóa tên thuốc để search trên Internet.
    Follows: knowledge for agent/web_search_normalizer_rules.py (drug_normalizer.py)
    Logic: Truncate at first invalid character based on whitelist.
    """
    if not text:
        return ""
        
    load_allowed_chars()
    if not _ALLOWED_CHARS:
        # Fallback if file missing: behave like matching normalizer or just return text?
        # Task implies strict following. If no allowed chars, result is empty.
        # But to be safe lets log and return generic clean
        print("Warning: No allowed chars loaded for search normalizer.")
        return ""

    result = []
    for char in text:
        if char in _ALLOWED_CHARS:
            result.append(char)
        else:
            # Stop at first invalid char
            break
            
    return "".join(result).strip()
