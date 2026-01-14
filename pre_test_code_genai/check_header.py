import csv

with open('fastapi-medical-app/dulieu_thuoc_playwright.csv', 'r', encoding='utf-8') as f:
    header = f.readline()
    print(f"Header Source: {header.strip()}")
    print(f"Header repr: {repr(header)}")
    
    f.seek(0)
    reader = csv.DictReader(f)
    print(f"Fieldnames: {reader.fieldnames}")
    
    first_row = next(reader)
    print(f"First Row Keys: {list(first_row.keys())}")
    print(f"First Row SDK: '{first_row.get('so_dang_ky')}'")
