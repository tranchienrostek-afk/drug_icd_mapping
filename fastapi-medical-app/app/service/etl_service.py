
import csv
import io
from app.services import DrugDbEngine

db = DrugDbEngine()

async def process_raw_log(batch_id: str, content: str):
    """
    Background Task: Process raw CSV content and update Knowledge Base.
    Expected CSV Format: drug_name, disease_name, [icd_code]
    """
    print(f"Starting ETL for batch {batch_id}")
    
    try:
        # Use StringIO to parse string as file
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        
        count = 0
        for row in reader:
            # Flexible column names
            drug = row.get('drug_name') or row.get('Drug Name') or row.get('thuoc')
            disease = row.get('disease_name') or row.get('Disease Name') or row.get('benh')
            icd = row.get('icd_code') or row.get('ICD Code') or row.get('icd')
            
            if drug and disease:
                db.upsert_knowledge_base(drug, disease, icd)
                count += 1
                
        print(f"Processed {count} records in batch {batch_id}")
        
    except Exception as e:
        print(f"ETL Error for batch {batch_id}: {e}")
