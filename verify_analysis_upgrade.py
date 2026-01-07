import urllib.request
import json
import sqlite3

BASE_URL = "http://localhost:8000"
DB_PATH = "fastapi-medical-app/app/database/medical.db"

def setup_mock_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. verified active link (Treats)
    cursor.execute("DELETE FROM drug_disease_links WHERE sdk = 'TEST-SDK-100'")
    cursor.execute("""
        INSERT INTO drug_disease_links (sdk, icd_code, coverage_type, treatment_note, status)
        VALUES ('TEST-SDK-100', 'A00.1', 'Thuốc điều trị', 'Found in DB', 'active')
    """)
    
    # 2. Refusal link (Refused)
    cursor.execute("DELETE FROM drug_disease_links WHERE sdk = 'TEST-SDK-200'")
    cursor.execute("""
        INSERT INTO drug_disease_links (sdk, icd_code, coverage_type, treatment_note, status)
        VALUES ('TEST-SDK-200', 'A00.1', 'Từ chối chi trả', 'Not supported', 'active')
    """)

    conn.commit()
    conn.close()
    print("Mock Data Setup Complete.")

def post_json(url, data):
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as f:
            return f.status, json.loads(f.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode('utf-8')}

def test_analysis():
    print("--- Testing Analysis API ---")
    payload = {
        "drugs": [
            "TestDrugOne (TEST-SDK-100)", # Should be VERIFIED
            "TestDrugTwo (TEST-SDK-200)", # Should be REFUSED
            "TestDrugThree (TEST-SDK-300)" # Unknown
        ],
        "diagnosis": [{"name": "Test Disease", "icd10": "A00.1"}]
    }
    
    # Note: The API first calls 'identify_drugs' which searches the DB. 
    # Whatever string we pass in drugs list is parsed.
    # To make sure 'TEST-SDK-100' is recognized as SDK, we might need real drug name or data in 'drugs' table.
    # But 'identify_drugs' might regex the SDK.
    # Let's hope the system is smart enough or we add a mock drug too?
    # Actually, identify_drugs does web search if not in DB.
    # So we should probably insert these drugs into 'drugs' table to avoid web search delay and ensuring SDK is captured.
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for i in [100, 200, 300]:
        cursor.execute(f"DELETE FROM drugs WHERE so_dang_ky = 'TEST-SDK-{i}'")
        cursor.execute(f"""
            INSERT INTO drugs (ten_thuoc, so_dang_ky, is_verified) 
            VALUES ('TestDrug{i}', 'TEST-SDK-{i}', 1)
        """)
    conn.commit()
    conn.close()

    status, resp = post_json(f"{BASE_URL}/api/v1/analysis/treatment-analysis", payload)
    print(f"Status: {status}")
    if status == 200:
        ai_res = resp.get('ai_analysis', {}).get('results', [])
        print("AI Results:")
        print(json.dumps(ai_res, indent=2, ensure_ascii=False))
        
        # Validation
        # Check for Verified
        # Note: The output format depends on LLM following instructions.
        # But we expect the verified one to be present.
    else:
        print(resp)

if __name__ == "__main__":
    setup_mock_data()
    test_analysis()
