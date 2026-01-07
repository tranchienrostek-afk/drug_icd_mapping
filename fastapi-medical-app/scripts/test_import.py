import sys
import os
sys.path.append('/app')
try:
    from app.service.web_crawler import search_drugs_online
    print("Import Successful")
except ImportError as e:
    print(f"Import Failed: {e}")
except Exception as e:
    print(f"Error: {e}")
