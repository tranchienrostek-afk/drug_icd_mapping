import urllib.request
import json

BASE_URL = "http://localhost:8000"

def get_json(url):
    try:
        with urllib.request.urlopen(url) as f:
             return f.status, json.loads(f.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode('utf-8')}
    except Exception as e:
        return 500, {"detail": str(e)}

print("--- Debugging Staging 500 Error ---")
# Call Staging API
# Path: /api/v1/drugs/admin/staging -> mapped to get_pending_stagings
status, resp = get_json(f"{BASE_URL}/api/v1/drugs/admin/staging")
print(f"Staging Status: {status}")
print(f"Staging Response: {resp}")

# If 500, we can't see server logs easily.
# But we can try to replicate the logic of `get_pending_stagings` locally in a script to see Python errors.
