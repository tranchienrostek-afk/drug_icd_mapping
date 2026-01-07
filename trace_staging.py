import sys
import os
import sqlite3

# Valid Absolute Path
DB_PATH = "c:/Users/Admin/Desktop/drug_icd_mapping/fastapi-medical-app/app/database/medical.db"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def trace_staging():
    print(f"--- Tracing get_pending_stagings ---")
    print(f"DB: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("DB FILE NOT FOUND!")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM drug_staging WHERE status = 'pending' ORDER BY id DESC")
        stagings = cursor.fetchall()
        print(f"Pending Items: {len(stagings)}")
        
        for item in stagings:
            print(f"Item: {item.get('ten_thuoc')} (ID: {item.get('id')})")
            # Replicate conflict logic
            conflict_id = item.get('conflict_id')
            if conflict_id:
                print(f"  > Checking conflict {conflict_id}")
                cursor.execute("SELECT ten_thuoc, so_dang_ky, hoat_chat FROM drugs WHERE rowid = ?", (conflict_id,))
                conflict_drug = cursor.fetchone()
                print(f"  > Conflict Drug: {conflict_drug}")
                item['conflict_info'] = conflict_drug
            else:
                item['conflict_info'] = None
                
        print("Trace Success.")
    except Exception as e:
        print("EXCEPTION CAUGHT:")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    trace_staging()
