# Test deployed API
import requests
import json
import time

def test_api():
    url = "http://localhost:8000/api/v1/drugs/identify"
    payload = {
        "drugs": ["Paracetamol 500mg"]  # Drug phổ biến, dễ test
    }
    
    print("="*60)
    print("TESTING DEPLOYED API (DOCKER)")
    print("="*60)
    print(f"Target: {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    start = time.time()
    try:
        response = requests.post(url, json=payload)
        elapsed = time.time() - start
        
        print(f"\nTime: {elapsed:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verify structure
            if "results" in data and len(data["results"]) > 0:
                print("\n✅ API Response Valid")
            else:
                print("\n⚠️ Empty results")
        else:
            print(f"\n❌ Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_api()
