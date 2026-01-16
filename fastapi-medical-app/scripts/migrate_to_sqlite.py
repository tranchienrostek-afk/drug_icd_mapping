import pandas as pd
import sqlite3
import os
from app.core.utils import normalize_text

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "app", "database", "drug_data_final.csv")
EXCEL_PATH = os.path.join(BASE_DIR, "app", "database", "icd_data_final_complete.xlsx")
DB_PATH = os.path.join(BASE_DIR, "app", "database", "medical.db")

def migrate():
    print(f"Loading data from {CSV_PATH}...")
    try:
        df_drugs = pd.read_csv(CSV_PATH, low_memory=False).fillna("")
    except FileNotFoundError:
        print("Drug CSV not found.")
        return

    # User Requirement: Clear 'so_dang_ky' and add 'is_verified'
    print("Processing Drug data schema...")
    df_drugs['so_dang_ky'] = ""
    df_drugs['is_verified'] = 0 # False/Integer 0

    # Ensure search index columns exist
    df_drugs['search_text'] = (df_drugs['ten_thuoc'] + " " + df_drugs['hoat_chat'] + " " + df_drugs['cong_ty_san_xuat']).apply(normalize_text)

    print(f"Loading data from {EXCEL_PATH}...")
    try:
        df_diseases = pd.read_excel(EXCEL_PATH).fillna("")
    except FileNotFoundError:
        print("Disease Excel not found.")
        return

    df_diseases['search_text'] = (df_diseases['icd_code'] + " " + df_diseases['disease_name'] + " " + df_diseases['slug']).apply(normalize_text)

    print(f"Connecting to SQLite: {DB_PATH}")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Start fresh

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- DRUGS ---
    print("Creating Drugs tables...")
    # Main table
    df_drugs.to_sql('drugs', conn, index=False, if_exists='replace')
    
    # FTS Table
    # We use porter tokenizer for better matching, or unicode61. 
    # For Vietnamese, unicode61 remove_diacritics=0 might be needed if we want exact, but we normalized text already.
    # Since we use 'search_text' which is normalized, simple tokenizer is fine.
    cursor.execute('''
        CREATE VIRTUAL TABLE drugs_fts USING fts5(
            ten_thuoc, 
            hoat_chat, 
            cong_ty_san_xuat, 
            search_text,
            content='drugs'
        )
    ''')
    
    # Populate FTS
    cursor.execute('''
        INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)
        SELECT rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text FROM drugs
    ''')

    # --- DISEASES ---
    print("Creating Diseases tables...")
    # Main table
    df_diseases.to_sql('diseases', conn, index=False, if_exists='replace')

    # FTS Table
    cursor.execute('''
        CREATE VIRTUAL TABLE diseases_fts USING fts5(
            icd_code,
            disease_name,
            slug,
            search_text,
            content='diseases'
        )
    ''')

    # Populate FTS
    cursor.execute('''
        INSERT INTO diseases_fts(rowid, icd_code, disease_name, slug, search_text)
        SELECT rowid, icd_code, disease_name, slug, search_text FROM diseases
    ''')

    # Triggers to keep FTS updated (Optional but good practice)
    # drug triggers
    cursor.execute('''
        CREATE TRIGGER drugs_ai AFTER INSERT ON drugs BEGIN
          INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)
          VALUES (new.rowid, new.ten_thuoc, new.hoat_chat, new.cong_ty_san_xuat, new.search_text);
        END;
    ''')
    # ... (omit update/delete triggers for brevity unless needed, focus on read-only optimization first)

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
