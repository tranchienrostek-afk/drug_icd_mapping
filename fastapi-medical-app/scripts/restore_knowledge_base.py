import sys
import os

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.service.etl_service import process_raw_log

CSV_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\test_data\data_drugs_feedback.csv"

def run_restore():
    print(f"--- Restore Knowledge Base ---")
    print(f"Source: {CSV_PATH}")
    
    if not os.path.exists(CSV_PATH):
        print("❌ CSV File not found!")
        return
        
    try:
        # Read content
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"Read {len(content)} bytes.")
        
        # Process
        stats = process_raw_log("RESTORE_BATCH_001", content)
        
        print(f"\n✅ Restore Complete.")
        print(stats)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_restore()
