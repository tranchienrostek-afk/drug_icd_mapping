import urllib.request
import json
import traceback

try:
    url = "http://localhost:8000/api/v1/admin/drugs?page=1&limit=5"
    print(f"Requesting: {url}")
    with urllib.request.urlopen(url) as response:
        print(f"Status: {response.getcode()}")
        content = response.read().decode('utf-8')
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print("Response is not JSON")
            print(content[:500])
            exit(1)
        
        if isinstance(data, dict):
             print("Response is a Dict.")
             print("Keys:", data.keys())
             if 'data' in data: 
                 items = data['data']
                 print(f"Items count: {len(items)}")
                 if len(items) > 0:
                     print("First item keys:", items[0].keys())
                     print("First item so_dang_ky:", items[0].get('so_dang_ky'))
                     print("First item full:", json.dumps(items[0], ensure_ascii=False))
        else:
            print("Response is not a dict:", type(data))

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
