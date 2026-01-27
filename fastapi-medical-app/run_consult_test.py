import requests
import json
import time

url = "http://localhost:8001/api/v1/consult_integrated"

payloads = [
    {
        "request_id": "test-traffic-01",
        "items": [
            {"id": "d1", "name": "Paracetamol 500mg", "amount": 0},
            {"id": "d2", "name": "Medovent 30mg", "amount": 0}
        ],
        "diagnoses": [
            {"code": "R51", "name": "Headache", "type": "MAIN"},
            {"code": "J00", "name": "Common Cold", "type": "MAIN"}
        ]
    },
    {
        "request_id": "test-traffic-02",
        "items": [
            {"id": "d3", "name": "Unknown Drug X", "amount": 0}
        ],
        "diagnoses": [
            {"code": "X99", "name": "Unknown Disease", "type": "MAIN"}
        ]
    }
]

for p in payloads:
    try:
        print(f"Sending request {p['request_id']}...")
        start = time.time()
        response = requests.post(url, json=p)
        latency = (time.time() - start) * 1000
        print(f"Status: {response.status_code}, Latency: {latency:.2f}ms")
        # print("Response:", response.json())
        print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")
