import requests
import json
import time

url = "http://localhost:8000/api/v1/drugs/agent-search"
headers = {"Content-Type": "application/json"}
data = {
    "drugs": ["Ludox - 200mg"]
}

print(f"Testing Agent Search Endpoint: {url}")
print(f"Payload: {data}")

try:
    start = time.time()
    response = requests.post(url, json=data, timeout=300) # Long timeout for agent
    duration = time.time() - start
    
    print(f"Status Code: {response.status_code}")
    print(f"Duration: {duration:.2f}s")
    
    if response.status_code == 200:
        print("Response Success:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print("Response Error:")
        print(response.text)

except Exception as e:
    print(f"Error: {e}")
