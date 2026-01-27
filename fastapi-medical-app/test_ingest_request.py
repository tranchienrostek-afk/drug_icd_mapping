import requests
import os

url = "http://localhost:8000/api/v1/data/ingest"
file_path = "test_ingest.csv"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

files = {'file': open(file_path, 'rb')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
