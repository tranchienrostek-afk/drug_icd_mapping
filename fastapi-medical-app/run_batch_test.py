import requests
import json
import os

# Path to the data file provided by user
DATA_FILE = r"C:\Users\Admin\Desktop\drug_icd_mapping\test_data\mapping_drugs_basic.json"
URL = "http://localhost:8000/api/v1/mapping/match"

def run_test():
    if not os.path.exists(DATA_FILE):
        print(f"Error: File found at {DATA_FILE}")
        return

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        
        # Add config if missing in file (user said schema *is* that, so it might lack it or have it)
        # The file content shown in history didn't have "config", but user mentioned schema has it.
        # I will blindly use the file content, but inject config if missing to ensure we use gpt-4o-mini
        if "config" not in payload:
             payload["config"] = {
                 "ai_model": "gpt-4o-mini",
                 "ai_temperature": 0.1
             }

        print(f"Sending request with {len(payload.get('claims', []))} claims...")
        response = requests.post(URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== SUMMARY ===")
            print(json.dumps(data.get("summary"), indent=2))
            
            print("\n=== RESULTS ===")
            print(f"{'STATUS':<15} | {'CLAIM':<30} | {'MEDICINE':<30} | {'CONF'}")
            print("-" * 90)
            for res in data.get("results", []):
                status = res.get("match_status")
                claim = res.get("claim_service")[:30]
                med = res.get("medicine_service") if res.get("medicine_service") else "---"
                med = med[:30]
                conf = res.get("confidence_score")
                print(f"{status:<15} | {claim:<30} | {med:<30} | {conf}")
                
            print("\n=== ANOMALIES ===")
            anomalies = data.get("anomalies", {})
            print(f"Claims without purchase: {len(anomalies.get('claim_without_purchase', []))}")
            print(f"Purchases without claim: {len(anomalies.get('purchase_without_claim', []))}")

        else:
            print(f"Failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    run_test()
