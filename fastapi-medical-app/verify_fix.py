from app.services import DrugDbEngine

try:
    db = DrugDbEngine()
    print("DrugDbEngine instantiated.")
    if hasattr(db, 'check_knowledge_base'):
        print("PASS: check_knowledge_base method exists.")
        res = db.check_knowledge_base([], [])
        print("Call result (empty):", res)
    else:
        print("FAIL: check_knowledge_base method MISSING.")

except Exception as e:
    print(f"Error: {e}")
