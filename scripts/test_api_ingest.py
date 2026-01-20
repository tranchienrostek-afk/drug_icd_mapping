import requests
import os

URL = "http://localhost:8000/api/v1/data/ingest"
FILE_PATH = r"C:\Users\Admin\Desktop\drug_icd_mapping\test_data\sample_ingest.csv"

def test_ingest():
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return

    print(f"Sending POST request to {URL}...")
    try:
        with open(FILE_PATH, 'rb') as f:
            files = {'file': ('sample_ingest.csv', f, 'text/csv')}
            response = requests.post(URL, files=files)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Ingest request successful.")
        else:
            print("❌ Ingest request failed.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ingest()
