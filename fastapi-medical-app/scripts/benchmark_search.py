import requests
import json
import time
import pandas as pd

URL = "http://localhost:8000/api/v1/drugs/identify"

TEST_CASES = [
    {"input": "Paracetamol 500mg", "type": "Legacy Data (Exact)"},
    {"input": "Sufentanil", "type": "New DataCore (Exact)"},
    {"input": "Tra Hoang Bach Phong", "type": "New Data (Normalized)"},
    {"input": "Paretamol", "type": "Fuzzy (Typo)"},
    {"input": "Acetaminophen", "type": "Synonym/Vector?"},
    {"input": "Thuoc giam dau Paracetamol", "type": "Context search"}
]

def run_benchmark():
    print(f"Running Benchmark on {URL}...\n")
    
    results_table = []
    
    for case in TEST_CASES:
        inp = case["input"]
        ptype = case["type"]
        
        print(f"Testing: '{inp}' ...", end=" ", flush=True)
        
        payload = {"drugs": [inp]}
        start = time.time()
        try:
            resp = requests.post(URL, json=payload, timeout=60)
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                
                if results:
                    item = results[0]
                    match_name = item.get("official_name")
                    confidence = item.get("confidence", 0)
                    source = item.get("source", "N/A")
                    sdk = item.get("sdk", "N/A")
                    
                    print(f"Found ({elapsed:.2f}s) - {source}")
                    results_table.append({
                        "Input": inp,
                        "Type": ptype,
                        "Time": f"{elapsed:.2f}s",
                        "Match": match_name[:30] + "..." if match_name and len(match_name)>30 else match_name,
                        "SDK": sdk,
                        "Source": source,
                        "Conf": confidence
                    })
                else:
                    print(f"Not Found ({elapsed:.2f}s)")
                    results_table.append({"Input": inp, "Type": ptype, "Time": f"{elapsed:.2f}s", "Status": "Not Found"})
            else:
                print(f"Error {resp.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")
            
    print("\n" + "="*100)
    print("BENCHMARK RESULTS (Task 018 Check)")
    print("="*100)
    df = pd.DataFrame(results_table)
    # Reorder columns if possible
    cols = ["Input", "Type", "Time", "Source", "Conf", "Match", "SDK"]
    # Filter only existing cols
    cols = [c for c in cols if c in df.columns]
    print(df[cols].to_string())
    print("="*100)

if __name__ == "__main__":
    run_benchmark()
