from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_treatment_analysis():
    payload = {
        "diagnosis": [
            {
                "icd10": "E11",
                "name": "Bệnh đái tháo đường không phụ thuộc insuline"
            },
            {
                "icd10": "I10",
                "name": "Bệnh Tăng huyết áp vô căn (nguyên phát)"
            }
        ],
        "drugs": [
            "Candesartan 16mg",
            "Metformin 500mg"
        ]
    }

    print(f"Sending request to /api/v1/analysis/treatment-analysis with payload:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    response = client.post("/api/v1/analysis/treatment-analysis", json=payload)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n--- Drugs Info ---")
        for drug in result.get("drugs_info", []):
            print(f"- {drug.get('ten_thuoc')} (SDK: {drug.get('sdk')}) - Status: {drug.get('status')}")
            
        print("\n--- Diseases Info ---")
        for disease in result.get("diseases_info", []):
            print(f"- {disease.get('name')} (ICD10: {disease.get('icd_code')}) - Status: {disease.get('status')}")
            
        print("\n--- AI Analysis ---")
        print(result.get("ai_analysis"))
        
        # Save response for inspection
        with open("test_analysis_response.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\nResponse saved to test_analysis_response.json")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_treatment_analysis()
