import json
import requests
import os
import sys

def run_datatest():
    # Path to test data
    test_file = os.path.join(os.path.dirname(__file__), "unittest", "datatest_mapping.json")
    
    if not os.path.exists(test_file):
        print(f"Error: Test file not found at {test_file}")
        return

    # Read test data
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"Error reading test file: {e}")
        return

    url = "http://localhost:8001/api/v1/mapping/match_v2"
    
    print(f"Running DataTest from: {test_file}")
    print(f"Target URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print("-" * 50)
        
        if response.status_code == 200:
            result = response.json()
            
            # Save result to file
            result_file = os.path.join(os.path.dirname(__file__), "unittest", "result_mapping.json")
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"Results saved to: {result_file}")
            
            print("Summary:")
            print(json.dumps(result.get("summary", {}), indent=2))
            
            print("\nMatches:")
            for match in result.get("results", []):
                print(f"✅ {match['claim_service']} <--> {match['medicine_service']}")
                print(f"   Confidence: {match['confidence_score']}")
                print(f"   Reasoning: {match['evidence']['notes']}")
                print("-" * 20)
                
            print("\nUnmatched/Anomalies:")
            for anom in result.get("anomalies", {}).get("claim_without_purchase", []):
                print(f"❌ {anom['service']} - {anom['reason']}")
        else:
            print("Error Response:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to localhost:8000. Is the server running?")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    run_datatest()
