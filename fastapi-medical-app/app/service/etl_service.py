
import csv
import io
from app.services import DrugDbEngine

db = DrugDbEngine()

import re

from app.core.classification import parse_csv_classification

def extract_treatment_type(row):
    """
    Delegate to core classification logic.
    Returns the standard 'value' key (e.g., 'valid', 'secondary drug').
    """
    phan_loai = row.get('phan_loai', '')
    tdv = row.get('tdv_feedback', '')
    
    result = parse_csv_classification(phan_loai, tdv)
    
    # If unknown, try fallback to old columns
    if result['value'] == 'unknown':
         return row.get('treatment_type') or row.get('Treatment Type') or row.get('group') or row.get('phan_nhom') or 'Unknown'
         
    return result['value']

async def process_raw_log(batch_id: str, content: str):
    """
    Background Task: Process raw CSV content and update Knowledge Base.
    Expected CSV Format: drug_name, disease_name, [icd_code], [phan_loai], [tdv_feedback]
    """
    print(f"Starting ETL for batch {batch_id}")
    
    try:
        # Use StringIO to parse string as file
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        
        count = 0
        for row in reader:
            # Flexible column names (Standardize to what's in logs.csv)
            drug = row.get('ten_thuoc') or row.get('drug_name') or row.get('Drug Name') or row.get('thuoc')
            # In logs.csv, disease is 'chuan_doan_ra_vien' or we map from ICD? 
            # Looking at csv: 'chuan_doan_ra_vien' is text. 'benh_phu' is complex json.
            # There is also implicit mapping.
            # But wait, looking at my view_file of logs.csv:
            # "chuan_doan_ra_vien","?column?","benh_phu"
            # "?column?" contains "J00 - ...". That seems to be the ICD+Name column.
            
            # Let's try to grab 'chuan_doan_ra_vien' or 'benh_phu' or standard columns
            disease = row.get('chuan_doan_ra_vien') or row.get('disease_name') or row.get('benh')
            
            # ICD is tricky in this CSV. "?column?" has "J00 - ...".
            # The DictReader might map "?column?" to the header key "?column?".
            raw_icd_field = row.get('?column?') or row.get('icd_code') or ""
            
            # Extract ICD code if possible (e.g., "J00 - ...")
            icd = raw_icd_field.split(' - ')[0].strip() if ' - ' in raw_icd_field else raw_icd_field
            
            group = extract_treatment_type(row)
            
            if drug and disease:
                db.insert_knowledge_interaction(drug, disease, group, icd, batch_id)
                count += 1
                
        print(f"Processed {count} records in batch {batch_id}")
        
    except Exception as e:
        print(f"ETL Error for batch {batch_id}: {e}")
