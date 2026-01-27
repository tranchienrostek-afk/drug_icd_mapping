
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "password")
host = os.getenv("POSTGRES_HOST", "localhost")

# Connect to default 'postgres' db
print(f"Connecting to 'postgres' DB on {host}...")
try:
    conn = psycopg2.connect(
        user=user, 
        password=password, 
        host=host, 
        dbname="postgres" # Default DB
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    db_name = os.getenv("POSTGRES_DB", "medical_db")
    
    # Check if exists
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Database '{db_name}' not found. Creating...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"✅ Database '{db_name}' created successfully!")
    else:
        print(f"ℹ️ Database '{db_name}' already exists.")
        
    conn.close()
except Exception as e:
    print(f"❌ Error creating database: {e}")
