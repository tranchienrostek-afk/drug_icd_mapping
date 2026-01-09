import requests
import json

url = "http://localhost:8000/api/v1/drugs/identify"
headers = {"Content-Type": "application/json"}
data = {
    "drugs": [
        "Panadol Extra", 
        "Thuốc Panadol 500mg",
        "Tên thuốc chứa dấu @ (sai)"
    ]
}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
