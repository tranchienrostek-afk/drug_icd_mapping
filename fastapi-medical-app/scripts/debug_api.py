
import requests
import json

API_URL = "http://localhost:8000/api/v1/drugs/identify"

def test_api():
    payload = {"drugs": ["Symbicort"]}
    print(f"Sending POST to {API_URL} with payload: {payload}")
    try:
        response = requests.post(API_URL, json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(response.text)
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    test_api()
