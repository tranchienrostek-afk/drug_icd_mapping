import urllib.request
import json
import time

BASE_URL = "http://localhost:8000"

def post_json(url, data):
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as f:
            resp = f.read().decode('utf-8')
            try:
                return f.status, json.loads(resp)
            except:
                print(f"RAW RESP OK: {resp}")
                return f.status, {}
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8')
        print(f"HTTP Error: {e.code}")
        print(f"ERROR BODY: {err}")
        try:
             return e.code, json.loads(err)
        except:
             return e.code, {"detail": err}

def get_json(url):
    try:
        with urllib.request.urlopen(url) as f:
             return f.status, json.loads(f.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode('utf-8')}

def test_link_flow():
    print("--- 1. Testing Link Creation with New Drug ---")
    payload = {
        "drug_name": "TestDrug_V1",
        "sdk": "TEST-SDK-001",
        "disease_name": "TestDisease_V1",
        "icd_code": "T00.1",
        "treatment_note": "Testing pending link",
        "coverage_type": "Thuốc điều trị",
        "created_by": "tester"
    }
    
    status, func_resp = post_json(f"{BASE_URL}/api/v1/drugs/knowledge/link", payload)
    print(f"Link Create Status: {status}")
    print(f"Link Create Body: {func_resp}")

if __name__ == "__main__":
    test_link_flow()
