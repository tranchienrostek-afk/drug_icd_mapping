import requests
import json
import os

def test_match_v2_with_data():
    url = "http://localhost:8000/api/v1/mapping/match_v2"
    data_path = r"c:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\unittest\datatest_mapping.json"
    
    if not os.path.exists(data_path):
        print(f"Error: Test data file not found at {data_path}")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    
    # Ensure config uses a valid model for the prompt logic if possible, 
    # though the service might override it or use env vars.
    if "config" in payload:
        payload["config"]["ai_model"] = "gpt-4o-mini"

    print(f"Sending request to {url}...")
    print(f"Using data from: {data_path}")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Save result to file
            output_path = r"c:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\unittest\result_mapping.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            print(f"\n✅ Results saved to: {output_path}")

            print("\nMatch Results Summary:")
            summary = result.get("summary", {})
            print(f"- Total Claims: {summary.get('total_claim_items')}")
            print(f"- Matched: {summary.get('matched_items')}")
            print(f"- Unmatched: {summary.get('unmatched_claims')}")
            print(f"- Risk Level: {summary.get('risk_level')}")
            
            print("\nDetailed Results:")
            for pair in result.get("results", []):
                print(f"[{pair.get('match_status')}] {pair.get('claim_service')} -> {pair.get('medicine_service')} (Score: {pair.get('confidence_score')})")
                print(f"   Reason: {pair.get('evidence', {}).get('notes')}")
            
            if result.get("anomalies"):
                print("\nAnomalies Detected:")
                for anomaly in result["anomalies"].get("claim_without_purchase", []):
                    print(f"- [Claim w/o Purchase] {anomaly.get('service')}: {anomaly.get('reason')}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error executing test: {e}")

if __name__ == "__main__":
    test_match_v2_with_data()
