
import os
import sys
from dotenv import load_dotenv

# Try loading from default (upwards search)
load_dotenv()

print("--- Environment Debug ---")
print(f"CWD: {os.getcwd()}")
print(f"POSTGRES_HOST: '{os.getenv('POSTGRES_HOST')}'")
print(f"POSTGRES_DB:   '{os.getenv('POSTGRES_DB')}'")
print(f"POSTGRES_USER: '{os.getenv('POSTGRES_USER')}'")
print(f"DB_TYPE:       '{os.getenv('DB_TYPE')}'")
print("-------------------------")
