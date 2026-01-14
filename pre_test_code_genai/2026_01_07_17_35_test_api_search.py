import requests
import json
import os
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1/drugs/identify"
OUTPUT_DIR = r"C:\Users\Admin\Desktop\drug_icd_mapping\tests\result_tests"
TIMESTAMP = datetime.now().strftime("%Y_%m_%d_%H_%M")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"result_test_{TIMESTAMP}.json")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Test Cases
TEST_CASES = [
    {
        "id": "TC01",
        "name": "Paracetamol",
        "description": "Basic search, expected to match DB or Web high confidence",
        "payload": {"drugs": ["Paracetamol"]}
    },
    {
        "id": "TC02",
        "name": "Symbicort 120 liều",
        "description": "Complex search, checks Detail Extraction (BUG-012 fix)",
        "payload": {"drugs": ["Symbicort 120 liều"]}
    },
    {
        "id": "TC03",
        "name": "NonExistentDrugXYZ",
        "description": "Unknown drug, check error handling/low confidence",
        "payload": {"drugs": ["NonExistentDrugXYZ123"]}
    },
    {
        "id": "TC04",
        "name": "Panadol Extra",
        "description": "Common brand name",
        "payload": {"drugs": ["Panadol Extra"]}
    }
]

def run_tests():
    results = []
    print(f"🚀 Starting API Test - {datetime.now()}")
    print(f"📂 Output File: {OUTPUT_FILE}")
    
    for case in TEST_CASES:
        print(f"\n▶️ Running {case['id']}: {case['name']}...")
        try:
            start_time = datetime.now()
            response = requests.post(API_URL, json=case['payload'], timeout=60)
            duration = (datetime.now() - start_time).total_seconds()
            
            result_data = {
                "test_id": case['id'],
                "input": case['name'],
                "description": case['description'],
                "status_code": response.status_code,
                "duration_seconds": duration,
                "response": response.json() if response.status_code == 200 else response.text,
                "timestamp": datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                print(f"   ✅ Success ({duration:.2f}s)")
            else:
                print(f"   ❌ Failed: Status {response.status_code}")
                
            results.append(result_data)
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                "test_id": case['id'],
                "input": case['name'],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    # Save Results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"summary": "API Drug Search Test", "cases": results}, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Tests Completed. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_tests()
