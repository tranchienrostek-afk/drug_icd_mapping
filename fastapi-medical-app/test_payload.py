import requests
import json

url = "http://localhost:8000/api/v1/mapping/match"

payload = {
  "request_id": "req-input-easy-001",
  "claims": [
    {
      "id": "clm-001",
      "service_name": "Augmentin 875+125",
      "amount": 185000
    },
    {
      "id": "clm-002",
      "service_name": "Paracetamol 500",
      "amount": 10000
    },
    {
      "id": "clm-003",
      "service_name": "Vitamin B Complex",
      "amount": 47000
    },
    {
      "id": "clm-004",
      "service_name": "Men tieu hoa",
      "amount": 35000
    }
  ],
  "medicines": [
    {
      "id": "med-101",
      "service_name": "Amoxicillin Clavulanate 875/125mg",
      "amount": 180000
    },
    {
      "id": "med-102",
      "service_name": "Paracetamol 500mg",
      "amount": 10000
    },
    {
      "id": "med-103",
      "service_name": "Vitamin B1 B6 B12",
      "amount": 47000
    },
    {
      "id": "med-104",
      "service_name": "Men tiêu hóa",
      "amount": 36000
    }
  ],
  "config": {
    "ai_model": "gpt-4o-mini"
  }
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        data = response.json()
        print(json.dumps(data.get("summary"), indent=2))
        for res in data.get("results", []):
            status = "✅" if res.get("match_status") == "matched" else "⚠️"
            print(f"{status} {res.get('claim_service')} -> {res.get('medicine_service')} ({res.get('match_status')})")
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Failed to call API: {e}")
