import requests
import json
import os

def run_test():
    url = "http://localhost:8001/api/v1/mapping/match"
    data_path = r"c:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\unittest\datatest_mapping.json"
    result_path = r"c:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app\unittest\result_mapping.json"
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"Success! Result saved to {result_path}")
    except Exception as e:
        print(f"Error calling API: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    run_test()
