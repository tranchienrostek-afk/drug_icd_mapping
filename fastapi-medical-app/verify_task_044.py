import requests
import json

url = "http://localhost:8000/api/v1/mapping/match"

payload = {
  "request_id": "req-verify-044",
  "claims": [
    {
      "id": "clm-betadine",
      "service_name": "Betadine suc hong 125ml",
      "amount": 75000
    },
    {
      "id": "clm-unmatched",
      "service_name": "Thuoc khong ton tai 12345", 
      "amount": 999999
    }
  ],
  "medicines": [
    {
      "id": "med-betadine",
      "service_name": "Betadine Gargle 125ml",
      "amount": 77000
    }
  ],
  "config": {
    "ai_model": "gpt-4o-mini"
  }
}

try:
    print("Sending verification request...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n=== RESPONSE SUMMARY ===")
        # summary = data.get("summary") 
        # print(summary) # Skip printing dict to avoid chars
        
        print("\n=== CHECKS ===")
        results = data.get("results", [])

        # CHECK 1: Betadine match
        betadine_match = next((r for r in results if r["claim_id"] == "clm-betadine"), None)
        if betadine_match and betadine_match["match_status"] in ["matched", "partially_matched", "weak_match"]:
            print("[SUCCESS] CHECK 1 PASSED: Betadine matched")
            print(f"Status: {betadine_match['match_status']}")
        else:
            print("[FAILURE] CHECK 1 FAILED: Betadine NOT matched")

        # CHECK 2: Unmatched filtering
        unmatched_in_results = next((r for r in results if r["claim_id"] == "clm-unmatched"), None)
        if not unmatched_in_results:
             print("[SUCCESS] CHECK 2 PASSED: Unmatched claim filtered from results")
        else:
             print("[FAILURE] CHECK 2 FAILED: Unmatched claim FOUND in results")
             
        # CHECK 3: Anomalies
        anomalies = data.get("anomalies", {}).get("claim_without_purchase", [])
        unmatched_anomaly = next((a for a in anomalies if a["id"] == "clm-unmatched"), None)
        if unmatched_anomaly:
            print("[SUCCESS] CHECK 3 PASSED: Unmatched claim found in Anomalies")
        else:
            print("[FAILURE] CHECK 3 FAILED: Unmatched claim NOT found in Anomalies")

    else:
        print(f"Error {response.status_code}")

except Exception as e:
    print(f"Exception: {e}")
