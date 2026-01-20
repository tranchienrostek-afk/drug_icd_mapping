import sqlite3
import csv
import json
import os
import sys
import re
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "app/database/medical.db")
CSV_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\test_data\data_drugs_feedback.csv"

def normalize_text(text):
    if not text: return ""
    return str(text).strip()

def normalize_classification(value: str) -> str:
    # Strict Expert Rules
    if not value: return json.dumps([])
    value = value.lower().strip()
    value = value.replace('[', '').replace(']', '').replace("'", "").replace('"', "").replace('{', '').replace('}', "")
    parts = [p.strip() for p in value.split(',') if p.strip()]
    
    # Rules
    if 'supplement' in parts and 'nodrug' not in parts: parts.insert(0, 'nodrug')
    if 'medical supplies' in parts and 'nodrug' not in parts: parts.insert(0, 'nodrug')
    if 'cosmeceuticals' in parts and 'nodrug' not in parts: parts.insert(0, 'nodrug')
    if 'medical equipment' in parts and 'nodrug' not in parts: parts.insert(0, 'nodrug')
    if 'invalid' in parts and 'drug' not in parts: parts.insert(0, 'drug')
    if 'valid' in parts:
        if 'drug' not in parts: parts.insert(0, 'drug')
        if 'main drug' not in parts and 'secondary drug' not in parts: parts.append('main drug')
    if 'secondary drug' in parts:
        if 'drug' not in parts: parts.insert(0, 'drug')
        if 'valid' not in parts: parts.insert(1, 'valid')

    return json.dumps(list(set(parts)))

def parse_icd(value):
    if not value: return "", ""
    # Matches "J00 - Viêm..."
    m = re.match(r'^([A-Z]\d+(?:\.\d+)?)\s*-\s*(.+)$', value)
    if m: return m.group(1).lower().strip(), m.group(2).strip()
    return "", value

def parse_benh_phu(value):
    if not value: return "", ""
    if value.startswith('{'):
        try:
            data = json.loads(value.replace('""', '"'))
            if isinstance(data, dict) and data:
                entry = list(data.values())[0]
                return entry.get('ma', '').lower(), entry.get('ten', '')
        except: pass
    return parse_icd(value)

def run_import():
    print(f"--- Quick Restore KB (Strict) ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Cache Diseases (ICD -> ID)
    print("Caching diseases...")
    cursor.execute("SELECT icd_code, id FROM diseases")
    disease_map = {row[0].lower(): row[1] for row in cursor.fetchall() if row[0]}
    print(f"Cached {len(disease_map)} diseases.")
    
    # Cache Drugs (Name -> ID) (Exact Match only for speed/safety)
    print("Caching drugs...")
    cursor.execute("SELECT ten_thuoc, id FROM drugs")
    drug_map = {row[0].lower().strip(): row[1] for row in cursor.fetchall() if row[0]}
    print(f"Cached {len(drug_map)} drugs.")

    print("Reading CSV...")
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        inserted = 0
        
        for row in reader:
            try:
                # 1. Parse Fields
                drug_name = normalize_text(row.get('ten_thuoc', '') or row.get('Tên thuốc', ''))
                drug_name_norm = drug_name.lower()
                
                icd_raw = normalize_text(row.get('?column?', '') or row.get('Mã ICD (Chính)', ''))
                icd_code, disease_name = parse_icd(icd_raw)
                
                benh_phu_raw = normalize_text(row.get('benh_phu', '') or row.get('Bệnh phụ', ''))
                sec_icd, sec_name = parse_benh_phu(benh_phu_raw)
                
                treatment_type = normalize_classification(row.get('phan_loai', ''))
                tdv_feedback = normalize_classification(row.get('tdv_feedback', ''))
                
                symptom = normalize_text(row.get('chuan_doan_ra_vien', ''))
                reason = normalize_text(row.get('Ly_do', ''))
                
                if not drug_name or not icd_code: continue

                # 2. Lookup
                drug_ref_id = drug_map.get(drug_name_norm)
                disease_ref_id = disease_map.get(icd_code)
                sec_ref_id = disease_map.get(sec_icd) if sec_icd else None
                
                # 3. Upsert
                # Check exist
                cursor.execute("SELECT id, frequency FROM knowledge_base WHERE drug_name_norm = ? AND disease_icd = ?", (drug_name_norm, icd_code))
                exist = cursor.fetchone()
                
                if exist:
                    new_freq = exist[1] + 1
                    cursor.execute("""
                        UPDATE knowledge_base SET 
                            frequency=?, drug_ref_id=?, disease_ref_id=?, 
                            treatment_type=?, tdv_feedback=?, last_updated=?
                        WHERE id=?
                    """, (new_freq, drug_ref_id, disease_ref_id, treatment_type, tdv_feedback, datetime.now(), exist[0]))
                else:
                    cursor.execute("""
                        INSERT INTO knowledge_base (
                            drug_name, drug_name_norm, drug_ref_id,
                            disease_icd, disease_name, disease_ref_id,
                            secondary_disease_icd, secondary_disease_name, secondary_disease_ref_id,
                            treatment_type, tdv_feedback, symptom, prescription_reason,
                            frequency, batch_id, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'QUICK_RESTORE', ?)
                    """, (
                        drug_name, drug_name_norm, drug_ref_id,
                        icd_code, disease_name, disease_ref_id,
                        sec_icd, sec_name, sec_ref_id,
                        treatment_type, tdv_feedback, symptom, reason, datetime.now()
                    ))
                    inserted += 1
                
                count += 1
                if count % 1000 == 0: print(f"Processed {count}...", end='\r')
                
            except Exception as e:
                # print(f"Row Error: {e}")
                pass
                
        conn.commit()
        print(f"\n✅ DONE. Processed {count} rows. Inserted/Updated.")
        conn.close()

if __name__ == "__main__":
    run_import()
