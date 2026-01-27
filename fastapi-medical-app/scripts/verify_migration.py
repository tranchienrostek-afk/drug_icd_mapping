
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    dbname=os.getenv("POSTGRES_DB"),
    host=os.getenv("POSTGRES_HOST")
)
cursor = conn.cursor()

tables = ["drugs", "diseases", "knowledge_base", "drug_disease_links"]
print("--- Migration Verification ---")
for table in tables:
    cursor.execute(f"SELECT count(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()
