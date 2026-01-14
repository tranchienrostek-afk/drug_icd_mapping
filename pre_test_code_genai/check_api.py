import urllib.request
import json

try:
    url = "http://localhost:8000/api/v1/drugs?page=1&limit=5"
    print(f"Requesting: {url}")
    with urllib.request.urlopen(url) as response:
        print(f"Status: {response.getcode()}")
        data = json.loads(response.read().decode('utf-8'))
        
        # Check if it's a list or dict
        if isinstance(data, list):
            print("Response is a List.")
            if len(data) > 0:
                print("First item keys:", data[0].keys())
        elif isinstance(data, dict):
             print("Response is a Dict.")
             print("Keys:", data.keys())
             if 'data' in data: # Pagination format
                 items = data['data']
                 print(f"Items count: {len(items)}")
                 if len(items) > 0:
                     print("First item keys:", items[0].keys())
                     print("First item sample:", json.dumps(items[0], ensure_ascii=False))
             elif 'results' in data:
                 print("Results found.")
                 items = data['results']
                 if len(items) > 0:
                     print("First item keys:", items[0].keys())
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
