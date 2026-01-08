import requests
import json
import time

API_URL = "http://localhost:8000/api/v1/drugs/identify"

# BUG-013 test drugs
test_payload = {
    "drugs": [
        "Ludox - 200mg",
        "Berodual 200 liều (xịt) - 10ml",
        "Symbicort 120 liều",
        "Althax - 120mg",
        "Hightamine"
    ]
}

def test_bug_013():
    print(f"Testing BUG-013 drugs with Google Search strategy...")
    print(f"Sending POST to {API_URL}")
    print(f"Payload: {json.dumps(test_payload, indent=2, ensure_ascii=False)}\n")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=test_payload, timeout=120)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Time Elapsed: {elapsed:.2f}s")
        print("\nResponse Body:")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Analysis
        if 'results' in result:
            results = result['results']
            found_count = sum(1 for r in results if r.get('sdk'))
            print(f"\n=== ANALYSIS ===")
            print(f"Total drugs tested: {len(results)}")
            print(f"Drugs with SDK found: {found_count}")
            print(f"Success rate: {found_count/len(results)*100:.1f}%")
            print(f"Average time per drug: {elapsed/len(results):.2f}s")
            
            if found_count >= 4:  # 80% of 5 drugs
                print("\n✓ BUG-013 RESOLVED: Target 80% success rate achieved!")
            else:
                print(f"\n✗ BUG-013 PARTIAL: Only {found_count}/5 drugs found (need 4/5)")
                
    except Exception as e:
        print(f"Error calling API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bug_013()
