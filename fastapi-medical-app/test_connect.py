
import psycopg2
import os
from dotenv import load_dotenv
import sys

load_dotenv()

host = os.getenv("POSTGRES_HOST", "BROKEN_DEFAULT")
db = os.getenv("POSTGRES_DB", "BROKEN_DEFAULT")
user = os.getenv("POSTGRES_USER", "BROKEN_DEFAULT")
password = os.getenv("POSTGRES_PASSWORD", "BROKEN_DEFAULT")

print(f"Attempting connection to: {host}:{db} as {user}")

try:
    conn = psycopg2.connect(
        host=host,
        dbname=db,
        user=user,
        password=password,
        port=5432,
        connect_timeout=5
    )
    print("SUCCESS: Connection established!")
    conn.close()
except Exception as e:
    print(f"FAILURE: {e}")
