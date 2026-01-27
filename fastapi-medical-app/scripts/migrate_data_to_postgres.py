
import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import sys
from dotenv import load_dotenv

# Load env vars FIRST so DatabaseCore sees DB_TYPE=postgres
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.core import DatabaseCore, DB_PATH

def migrate():
    print("🚀 Starting Data Migration: SQLite -> Postgres")
    
    # 1. Connect SQLite (Source)
    sqlite_path = DB_PATH
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite DB not found at {sqlite_path}")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_curr = sqlite_conn.cursor()
    print(f"✅ Connected to SQLite: {sqlite_path}")

    # 2. Connect Postgres (Target)
    try:
        pg_conn = psycopg2.connect(
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            dbname=os.getenv("POSTGRES_DB", "medical_db"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        pg_curr = pg_conn.cursor()
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to Postgres: {e}")
        return

    # 3. Ensure Postgres Tables Exist (Using Refactored Core)
    print("   Init DatabaseCore to ensure schema...")
    # This will trigger _init_postgres() because DB_TYPE=postgres (loaded from .env)
    core = DatabaseCore() 
    
    # Tables to migrate
    tables = [
        "drugs", 
        "diseases",
        "drug_staging",
        "drug_history",
        "drug_staging_history",
        "drug_disease_links",
        "knowledge_base",
        "raw_logs",
        "api_logs"
    ]

    for table in tables:
        print(f"\n📦 Migrating table: {table}...")
        try:
            # Check fields in SQLite
            sqlite_curr.execute(f"SELECT * FROM {table} LIMIT 1")
            col_names = [description[0] for description in sqlite_curr.description]
            
            # Fetch Data
            sqlite_curr.execute(f"SELECT * FROM {table}")
            rows = sqlite_curr.fetchall()
            
            if not rows:
                print(f"   ⚠️ No data in {table}, skipping.")
                continue

            print(f"   found {len(rows)} records.")
            
            # Filter columns that might not exist in target or causing issues
            # We assume schema compatibility from Core Refactor
            # Excluding 'id' if we want serial to auto-inc? 
            # NO, we must preserve IDs to keep relationships (links, logs, etc.)
            
            columns_str = ", ".join(col_names)
            placeholders = ", ".join(["%s"] * len(col_names))
            
            query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
            if table == "diseases":
                 query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
            
            # Convert rows to tuple data
            data = []
            for row in rows:
                vals = []
                for col in col_names:
                    val = row[col]
                    # Handle boolean conversion if needed (SQLite 0/1 -> PG Integer/Boolean)
                    # Our PG schema uses Integer for is_verified, so 0/1 is fine.
                    vals.append(val)
                data.append(tuple(vals))

            # Batch Insert
            execute_batch(pg_curr, query, data)
            pg_conn.commit()
            print(f"   ✅ Successfully migrated {len(data)} records.")

            # Update Sequence if ID is Serial
            if table != "diseases": # diseases has TEXT ID
                pg_curr.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(max(id), 1)) FROM {table}")
                pg_conn.commit()
                print("   🔄 Sequence updated.")

        except sqlite3.OperationalError as e:
            print(f"   ⚠️ SQLite Error (table might not exist): {e}")
        except Exception as e:
            print(f"   ❌ Migration Failed for {table}: {e}")
            pg_conn.rollback()

    print("\n🎉 Migration Complete!")
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
