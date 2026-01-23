import requests
import json

url = "http://localhost:8000/api/v1/consult_integrated"

payload = {
  "diagnoses": [
    {
      "code": "J00",
      "name": "Viêm mũi họng cấp",
      "type": "MAIN"
    }
  ],
  "items": [
    {
      "id": "916b023e-a5cb-4e8e-b0d4-309f2d02d778",
      "name": "natriclorid srk saltmax 0 45g 50ml x 100ml"
    }
  ],
  "request_id": "BT/24594",
  "symptom": "Viêm đường hô hấp - Viêm mũi họng cấp - Nhiễm RSV"
}

try:
    print("Sending request...")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        # Validation
        res = data['results'][0]
        if res['category'] == 'nodrug' and res['validity'] == "":
             print("\n✅ Verification PASSED: Category is 'nodrug' and Validity is empty.")
        else:
             print("\n❌ Verification FAILED: Unexpected result.")
             print(f"Category: {res.get('category')}")
             print(f"Validity: {res.get('validity')}")
    else:
        print("Error:", response.text)

except Exception as e:
    print(f"Exception: {e}")
