import asyncio
import time
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fastapi-medical-app')))

from app.service.crawler.main import scrape_drug_web_advanced
from app.utils import normalize_text, normalize_name

# Test Data
DRUGS = [
    "Berodual",        # Short name
    "Panadol Extra",   # Common, fast
    "Augmentin 1g",    # With concentration
    "Efferalgan 500mg",# With dose
    "Zinnat 500mg"     # Another antibiotic
]

RESULT_DIR = "result_test"
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

LOG_FILE = os.path.join(RESULT_DIR, f"benchmark_{int(time.time())}.log")

def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def run_benchmark():
    log(f"--- START BENCHMARK {time.ctime()} ---")
    
    # 1. Verify Normalization
    log("\n[Test 1] Normalization Check")
    cases = ["Berodual 200 liều", "Thuốc A+B (500mg)"]
    for c in cases:
        norm = normalize_text(c)
        log(f"Input: '{c}' -> Norm: '{norm}'")
        if "ieu" not in norm and "liều" in c.lower():
             log("!! ERROR: Normalization corrupted 'liều'")

    # 2. Performance Search
    log("\n[Test 2] Speed Test (Target < 45s for 5 items)")
    start_total = time.time()
    
    tasks = []
    for d in DRUGS:
        # Launch concurrently as real API? 
        # API usually does sequential per request, but user might send parallel requests.
        # Task spec says "Total search time for 5 drugs < 45s".
        # This implies either parallel batch or very fast sequential.
        # Let's test SEQUENTIAL first as that's the baseline use case for single user multiple queries? 
        # Actually API is likely hit concurrently. 
        # But if the requirement is < 45s TOTAL for 5 drugs, and sequential takes 5 mins (300s), then sequential must be 9s/drug?
        # Or parallel < 45s?
        # Given "Sequential site scraping" was a bottleneck, we improved site concurrency.
        # Let's run SEQUENTIAL loop here to demonstrate per-drug speed improvement.
        pass

    results = []
    for d in DRUGS:
        t0 = time.time()
        log(f"Searching: {d}...")
        try:
            res = await scrape_drug_web_advanced(d, headless=True)
            elapsed = time.time() - t0
            status = "FOUND" if res.get("so_dang_ky") else "NOT_FOUND"
            log(f" -> {d}: {elapsed:.2f}s | {status} | SDK: {res.get('so_dang_ky')}")
            results.append({"drug": d, "time": elapsed, "status": status})
        except Exception as e:
            log(f" -> {d}: ERROR {e}")

    total_time = time.time() - start_total
    log(f"\nTotal Time: {total_time:.2f}s")
    
    if total_time < 45:
        log("✅ PASS: < 45s")
    else:
        log("❌ FAIL: > 45s")

    log("--- END BENCHMARK ---")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
