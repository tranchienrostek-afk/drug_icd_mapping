import sqlite3
import unicodedata
import re
import os
import sys

# Re-implement utils matching logic to be 100% sure what we are running here
# OR import it if path allows. Let's import it.
sys.path.append(os.getcwd())
from app.core.utils import normalize_text

conn = sqlite3.connect('app/database/medical.db')
cursor = conn.cursor()

dn = 'Ambroxol (Drenoxol)'
norm = normalize_text(dn)
print(f"Input: '{dn}'")
print(f"Norm Input: '{norm}'")

print("-" * 20)
print("Searching for drug 'Ambroxol' in KB...")
cursor.execute("SELECT drug_name, drug_name_norm, disease_icd, treatment_type, tdv_feedback FROM knowledge_base WHERE drug_name LIKE '%Ambroxol%'")
rows = cursor.fetchall()
print(f"Found {len(rows)} rows.")
for r in rows:
    print(r)

print("-" * 20)
print("Checking exact match for Norm Input + J00...")
cursor.execute("SELECT * FROM knowledge_base WHERE drug_name_norm = ? AND disease_icd = 'J00'", (norm,))
matches = cursor.fetchall()
print(f"Exact matches: {len(matches)}")
for m in matches:
    print(m)

conn.close()
