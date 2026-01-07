import logging
import os
import re

# --- LOGGING SETUP ---
LOG_DIR = "app/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure Logger
logger = logging.getLogger("scraper")
logger.setLevel(logging.INFO)

# Avoid adding handlers multiple times if module is reloaded
if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File Handler
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "scraper.log"), encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Stream Handler (Console)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

# --- SCREENSHOT UTILS ---
SCREENSHOT_DIR = "app/logs/screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

def parse_drug_info(raw_text):
    """Extract structured info from raw text using Regex"""
    data = {
        "so_dang_ky": None,
        "hoat_chat": None,
        "cong_ty_san_xuat": None,
        "chi_dinh": None, 
        "tu_dong_nghia": None
    }
    
    if not raw_text:
        return data

    # SDK Pattern: VN-1234-56, VD-..., V..., QL...
    # Robust patterns for various formats
    patterns = [
        r'(?:SĐK|Số đăng ký|SĐK|SDK|Reg\.No)[:\.]?\s*([A-Z0-9\-\/]{5,20})', # Min 5 chars
        r'(VN-\d{4,10}-\d{2}|VD-\d{4,10}-\d{2}|QLD-\d+-\d+|GC-\d+-\d+|VNA-\d+-\d+|VNB-\d+-\d+)', # Common Patterns
        r'([A-Z]{1,3}-\d{4,10}-\d{2})' # General Pattern
    ]
    
    for p in patterns:
        match = re.search(p, raw_text, re.IGNORECASE)
        if match:
            data["so_dang_ky"] = match.group(1).strip().strip(':').strip('.')
            break
            
    # Simple direct SDK pattern if no prefix found
    if not data["so_dang_ky"]:
        # Match something like VD-12345-12 or VN-123456-12
        match = re.search(r'([A-Z]{1,3}-\d{4,10}-\d{2})', raw_text)
        if match:
             data["so_dang_ky"] = match.group(1)

    # Hoat Chat
    hc_match = re.search(r"(?:Hoạt chất|Thành phần)[:\.]?\s*(.+?)(?:\n|$)", raw_text, re.IGNORECASE)
    if hc_match:
        data["hoat_chat"] = hc_match.group(1).strip()
        
    # Cong Ty
    ct_match = re.search(r"(?:Công ty|Nhà) sản xuất[:\.]?\s*(.+?)(?:\n|$)", raw_text, re.IGNORECASE)
    if ct_match:
        data["cong_ty_san_xuat"] = ct_match.group(1).strip()
        
    return data
