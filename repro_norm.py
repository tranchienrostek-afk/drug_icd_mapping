import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'fastapi-medical-app')))

from app.utils import normalize_text, normalize_name, normalize_drug_name

texts = [
    "Berodual 200 liều",
    "Berodual 200 Liều",
    "Thuốc ABC (10ml)"
]

print("--- Normalization Debug ---")
for t in texts:
    print(f"\nInput: '{t}'")
    try:
        n_text = normalize_text(t)
        print(f"normalize_text: '{n_text}'")
    except Exception as e:
        print(f"normalize_text error: {e}")

    try:
        n_name = normalize_name(t)
        print(f"normalize_name: '{n_name}'")
    except Exception as e:
        print(f"normalize_name error: {e}")

    try:
        n_drug = normalize_drug_name(t)
        print(f"normalize_drug_name: '{n_drug}'")
    except Exception as e:
        print(f"normalize_drug_name error: {e}")
