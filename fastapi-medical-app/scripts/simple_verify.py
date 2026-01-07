import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from app.services import DrugDbEngine
    print("Import successful")
    db = DrugDbEngine()
    print("DB Init successful")
except Exception as e:
    print(f"Error: {e}")
