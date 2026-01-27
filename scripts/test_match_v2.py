import requests
import json

def test_match_v2():
    url = "http://localhost:8000/api/v1/mapping/match_v2"
    
    payload = {
        "request_id": "test-v2-direct-ai",
        "claims": [
            {
                "id": "1",
                "service": "MEDOVENT 30 10X10",
                "amount": 10000
            },
            {
                "id": "2",
                "service": "PANTOLOC 40MG TAKEDA 1X7",
                "amount": 10000
            },
            {
                "id": "3",
                "service": "Thăm dò chức năng",
                "amount": 10000
            }
        ],
        "medicine": [
            {
                "id": "1",
                "service": "Ambroxol hydrochloride (Medovent 30mg)",
                "amount": 0
            },
            {
                "id": "2",
                "service": "Pantoprazole (dưới dạng Pantoprazole sodium sesquihydrate)(Pantoloc 40mg)",
                "amount": 0
            }
        ],
        "config": {
            "ai_model": "gpt-4o-mini"
        }
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Results:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    test_match_v2()
