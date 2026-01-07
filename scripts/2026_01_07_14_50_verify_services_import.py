import sys
import os

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'fastapi-medical-app'))

try:
    from app.services import DrugDbEngine, search_icd_online
    print("SUCCESS: app.services imported correctly.")
    print("SUCCESS: search_icd_online imported correctly.")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Other Error: {e}")
    sys.exit(1)
