import sys
import os

# Set execution path to the directory of the script to avoid import errors if any relative imports existed (though none were seen)
script_dir = r"C:\Users\Admin\Desktop\drug_icd_mapping\knowledge for agent"
sys.path.append(script_dir)

# Import the functionality from the knowledge script
# Since we cannot modify the original file, we import the function
try:
    from trungtamthuoc_extract import crawl_one
except ImportError:
    # Fallback if path handling is strict
    import importlib.util
    spec = importlib.util.spec_from_file_location("trungtamthuoc_extract", os.path.join(script_dir, "trungtamthuoc_extract.py"))
    trungtamthuoc_extract = importlib.util.module_from_spec(spec)
    sys.modules["trungtamthuoc_extract"] = trungtamthuoc_extract
    spec.loader.exec_module(trungtamthuoc_extract)
    crawl_one = trungtamthuoc_extract.crawl_one

# Test Info
target_url = "https://trungtamthuoc.com/ludox-200mg"

print(f"--- Running Knowledge Script: trungtamthuoc_extract.py ---")
print(f"Target URL: {target_url}")

result = crawl_one(target_url)

print("\n--- RESULTS ---")
from pprint import pprint
pprint(result)
