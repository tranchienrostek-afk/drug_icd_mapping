from app.services import DiseaseDbEngine

db = DiseaseDbEngine()
print("Testing Disease Search...")

test_cases = [
    {"name": "Bệnh đái tháo đường không phụ thuộc insuline", "icd": ""},
    {"name": "", "icd": "E11"},
    {"name": "Đau đầu", "icd": ""},
    {"name": "Non-existent Disease", "icd": ""}
]

for case in test_cases:
    print(f"\nSearching: Name='{case['name']}', ICD='{case['icd']}'")
    result = db.search(case['name'], case['icd'])
    if result:
        print(f"FOUND: ID={result['data']['id']}, Name={result['data']['disease_name']}, ICD={result['data']['icd_code']}")
        print(f"Source: {result['source']}")
    else:
        print("NOT FOUND")
