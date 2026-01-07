import urllib.request
import urllib.parse
import sqlite3
import json
import time

BASE_URL = "http://localhost:8000"
DB_PATH = "app/database/medical.db"

def make_request(endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
        
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Request Error: {e}")
        raise

def setup_test_data():
    """Insert a test drug directly into DB"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Clean up first
        cursor.execute("DELETE FROM drugs WHERE so_dang_ky = 'VN-TEST-ADVANCED'")
        
        # Insert Verified Drug
        cursor.execute("""
            INSERT INTO drugs (ten_thuoc, so_dang_ky, hoat_chat, is_verified, search_text)
            VALUES ('TestDrugAdvanced', 'VN-TEST-ADVANCED', 'TestIngredient', 1, 'testdrugadvanced testingredient')
        """)
        conn.commit()
        print("[Setup] Inserted TestDrugAdvanced into DB.")
    except Exception as e:
        print(f"[Setup] Error: {e}")
    finally:
        conn.close()

def test_identify_exact():
    print("\n[Test] Identify Exact Match...")
    payload = {"drugs": ["TestDrugAdvanced"]}
    try:
        data = make_request("/api/v1/drugs/identify", payload)
        result = data['results'][0]
        
        print(f"Result: {result.get('official_name')} - Source: {result.get('source')} - Conf: {result.get('confidence')}")
        
        if result.get('sdk') == 'VN-TEST-ADVANCED' and result.get('confidence') == 1.0:
            print(">>> PASS: Exact Match Found.")
        else:
            print(">>> FAIL: Exact Match not found or low confidence.")
            
    except Exception as e:
        print(f">>> ERROR: {e}")

def test_identify_web():
    print("\n[Test] Identify Web Search (Panadol)...")
    payload = {"drugs": ["Panadol"]}
    try:
        # This might take time due to scraping
        start = time.time()
        data = make_request("/api/v1/drugs/identify", payload)
        elapsed = time.time() - start
        
        result = data['results'][0]
        
        print(f"Result: {result.get('official_name')} - Source: {result.get('source')} - Conf: {result.get('confidence')} - Time: {elapsed:.2f}s")
        
        if result.get('source') == 'Web' or 'Web Search' in str(result.get('source')):
             print(">>> PASS: Web Search returned result.")
        else:
             print(">>> FAIL: Web Search failed or returned DB result.")
             
    except Exception as e:
        print(f">>> ERROR: {e}")

if __name__ == "__main__":
    setup_test_data()
    test_identify_exact()
    test_identify_web()
