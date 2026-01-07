import sys
import os
import sqlite3
import json
import urllib.request
import urllib.parse
import random
from pprint import pprint

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import DrugDbEngine

DB_PATH = "app/database/medical.db"
BASE_URL = "http://localhost:8000/api/v1"

def reset_db_for_test():
    """Clear test data from DB"""
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM drugs WHERE so_dang_ky = 'TEST-SDK-001'")
            cursor.execute("DELETE FROM drug_staging WHERE so_dang_ky = 'TEST-SDK-001'")
            cursor.execute("DELETE FROM drug_history WHERE so_dang_ky = 'TEST-SDK-001'")
            conn.commit()
            print("[-] DB Reset for TEST-SDK-001")
        except:
             pass
        finally:
            conn.close()

def make_request(method, url, data=None):
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, method=method)
        req.add_header('Content-Type', 'application/json')
    else:
        req = urllib.request.Request(url, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.getcode(), json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)
    except Exception as e:
        print(f"Request Error: {e}")
        return 0, {}

def test_workflow():
    db = DrugDbEngine() 
    # This should trigger _ensure_tables
    
    sdk = f"TEST-SDK-{random.randint(1000, 9999)}"
    print(f"\n--- 1. ADD NEW DRUG ({sdk}) ---")
    payload_new = {
        "ten_thuoc": "Test Drug A",
        "so_dang_ky": sdk,
        "hoat_chat": "Test Ingredient",
        "chi_dinh": "Original Indication",
        "cong_ty_san_xuat": "Test Corp",
        "tu_dong_nghia": "Test Alias",
        "modified_by": "tester"
    }
    
    code, data = make_request("POST", f"{BASE_URL}/drugs/confirm", payload_new)
    print(f"Response: {code} - {data}")
    if code == 200 and data.get('status') == 'success':
        print("[PASS] New drug added.")
    else:
        print("[FAIL] New drug add failed.")

    print("\n--- 2. ADD CONFLICT DRUG (UPDATE ATTEMPT) ---")
    payload_conflict = payload_new.copy()
    payload_conflict["chi_dinh"] = "Updated Indication (Pending)"
    
    code, data = make_request("POST", f"{BASE_URL}/drugs/confirm", payload_conflict)
    print(f"Response: {code} - {data}")
    
    staging_id = None
    if data.get('status') == 'pending_confirmation':
        staging_id = data.get('staging_id')
        print(f"[PASS] Conflict detected, saved to staging ID: {staging_id}")
    else:
        print("[FAIL] Conflict not detected or wrong status.")

    if not staging_id: return

    print("\n--- 3. CHECK STAGING LIST ---")
    url_staging = f"{BASE_URL}/drugs/admin/staging"
    code, items = make_request("GET", url_staging)
    print(f"Staging List Response: {code}")
    found = False
    if isinstance(items, list):
        for item in items:
            if item['id'] == staging_id:
                found = True
                print(f"Found staging item: {item['ten_thuoc']} - {item['status']}")
                break
    
    if found:
        print("[PASS] Staging item found in list.")
    else:
        print("[FAIL] Staging item NOT found in list.")

    print("\n--- 4. APPROVE STAGING ---")
    url_approve = f"{BASE_URL}/drugs/admin/approve/{staging_id}?user=tester_admin"
    code, data = make_request("POST", url_approve)
    print(f"Approve Response: {code} - {data}")
    
    if data.get('status') == 'success':
        print("[PASS] Approval successful.")
    else:
        print("[FAIL] Approval failed.")

    print("\n--- 5. VERIFY UPDATE AND HISTORY ---")
    # Check Main DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM drugs WHERE so_dang_ky = ?", (sdk,))
    row = cursor.fetchone()
    if row and row['chi_dinh'] == "Updated Indication (Pending)":
        print("[PASS] Main table updated correctly.")
    else:
        print(f"[FAIL] Main table not updated. Current: {row['chi_dinh'] if row else 'None'}")

    cursor.execute("SELECT * FROM drug_history WHERE so_dang_ky = ?", (sdk,))
    h_row = cursor.fetchone()
    if h_row and h_row['chi_dinh'] == "Original Indication":
        print("[PASS] History table preserved original data.")
    else:
        print("[FAIL] History table missing or wrong data.")
        
    conn.close()

if __name__ == "__main__":
    reset_db_for_test()
    try:
        test_workflow()
    finally:
        # Cleanup
        reset_db_for_test()
