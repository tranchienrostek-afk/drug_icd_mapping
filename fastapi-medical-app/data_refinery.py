import sqlite3
import re
import html
from app.utils import normalize_text

DB_PATH = "app/database/medical.db"

# --- RULES & DICTIONARIES ---
PACKAGING_PATTERNS = [
    r'\((hộp|vỉ|lọ|chai|tuýp|ống).*?\)',  # (hộp 10 vỉ...)
    r'\((box|bottle|tube|ampoule).*?\)',
    r'\d+\s*(viên|ml|g|mg).*?$',         # End with ...500mg (sometimes part of name, be careful)
]

THERAPEUTIC_MAP = {
    "khang_sinh": ["amoxicillin", "cef", "mycin", "cilin", "floxacin", "cyclin"],
    "giam_dau_ha_sot": ["paracetamol", "ibuprofen", "aspirin", "diclofenac", "tramadol"],
    "tim_mach": ["pril", "sartan", "lol", "statin", "amlodipin", "nifedipin"],
    "tieu_duong": ["metformin", "gliclazide", "insulin", "glimepiride"],
    "da_day": ["omeprazol", "lansoprazol", "esomeprazol", "aluminium", "magnesium"],
    "di_ung": ["loratadin", "cetirizin", "fexofenadin", "chlorpheniramine"],
}

CATEGORY_NAMES = {
    "khang_sinh": "Kháng sinh",
    "giam_dau_ha_sot": "Giảm đau - Hạ sốt",
    "tim_mach": "Tim mạch - Huyết áp",
    "tieu_duong": "Tiểu đường",
    "da_day": "Tiêu hóa - Dạ dày",
    "di_ung": "Dị ứng - Kháng Histamin"
}

def clean_html(text):
    if not text: return ""
    clean = re.sub(r'<[^>]+>', ' ', text) # Remove tags
    clean = html.unescape(clean)          # Unescape &amp; etc
    clean = re.sub(r'\s+', ' ', clean).strip() # Normalize whitespace
    return clean

def normalize_name(name):
    if not name: return "", ""
    
    packaging = ""
    clean_name = name
    
    # Extract packaging in parentheses
    for pattern in PACKAGING_PATTERNS:
        match = re.search(pattern, clean_name, re.IGNORECASE)
        if match:
            packaging = match.group(0)
            clean_name = clean_name.replace(packaging, "").strip()
            # Clean up double spaces or trailing punctuation
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            clean_name = clean_name.strip("-").strip()
            break
            
    # Title Case
    clean_name = clean_name.title()
    return clean_name, packaging

def infer_category(ingredient):
    if not ingredient: return "Khác"
    ing_lower = ingredient.lower()
    
    for key, keywords in THERAPEUTIC_MAP.items():
        for kw in keywords:
            if kw in ing_lower:
                return CATEGORY_NAMES[key]
                
    return "Khác"

def run_refinery():
    print("Starting Data Refinery...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.create_function("normalize_text", 1, normalize_text)
    cursor = conn.cursor()

    try:
        # 1. Add new columns if not exist
        try:
            cursor.execute("ALTER TABLE drugs ADD COLUMN nhom_duoc_ly TEXT")
            print("Added column 'nhom_duoc_ly'")
        except sqlite3.OperationalError:
            pass # Column exists
            
        try:
            cursor.execute("ALTER TABLE drugs ADD COLUMN quy_cach TEXT")
            print("Added column 'quy_cach'")
        except sqlite3.OperationalError:
            pass

        # 2. Fetch all drugs
        cursor.execute("SELECT rowid, ten_thuoc, chi_dinh, hoat_chat FROM drugs")
        rows = cursor.fetchall()
        
        print(f"Processing {len(rows)} drugs...")
        
        updates = []
        for row in rows:
            row_id = row['rowid']
            old_name = row['ten_thuoc']
            old_desc = row['chi_dinh']
            ingredient = row['hoat_chat']
            
            # Process
            new_name, packaging = normalize_name(old_name)
            new_desc = clean_html(old_desc)
            category = infer_category(ingredient)
            
            updates.append((new_name, packaging, new_desc, category, row_id))
            
        # 3. Batch Update
        cursor.executemany("""
            UPDATE drugs 
            SET ten_thuoc = ?, quy_cach = ?, chi_dinh = ?, nhom_duoc_ly = ?
            WHERE rowid = ?
        """, updates)
        
        # 4. Update FTS
        # Simplified: Just rebuild FTS for changed descriptions/names? 
        # For simplicity, we assume FTS triggers or periodic rebuilds handle this, 
        # or we manually update FTS here. Let's do a manual FTS update for safety.
        print("Updating FTS Index...")
        cursor.execute("DELETE FROM drugs_fts")
        cursor.execute("""
            INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, search_text)
            SELECT rowid, ten_thuoc, hoat_chat, normalize_text(ten_thuoc || ' ' || hoat_chat || ' ' || so_dang_ky)
            FROM drugs
        """)
        
        conn.commit()
        print(f"Successfully refined {len(updates)} records.")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_refinery()
