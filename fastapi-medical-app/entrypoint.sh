#!/bin/bash
set -e

# --- 1. Wait for PostgreSQL ---
echo "[Entrypoint] Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."

# Function to check internal connection
wait_for_db() {
  python -c "
import psycopg2, os, time, sys
host = os.getenv('POSTGRES_HOST', 'postgres')
user = os.getenv('POSTGRES_USER', 'postgres')
password = os.getenv('POSTGRES_PASSWORD', 'password')
db = os.getenv('POSTGRES_DB', 'medical_db')

for i in range(30):
    try:
        conn = psycopg2.connect(host=host, user=user, password=password, dbname=db)
        conn.close()
        print('DB Connected!')
        sys.exit(0)
    except Exception as e:
        print(f'Waiting... ({e})')
        time.sleep(2)
sys.exit(1)
"
}

if wait_for_db; then
    echo "[Entrypoint] Database is ready."
else
    echo "[Entrypoint] Error: Database did not start."
    exit 1
fi

# --- 2. Auto-Migrate / Init Schema ---
echo "[Entrypoint] 🚀 Running Schema Initialization / Migration..."

# Check if we need to run specific migration script or just rely on App startup
# app/database/core.py automatically initializes schema on first connection.
# But trigger creation requires superuser or specific run.
# Let's run a check script or the app itself triggers it.

# For robustness, we can try running the create_db script logic if needed,
# but typically the app handles "CREATE TABLE IF NOT EXISTS".

# Force init by instantiating DatabaseCore once
python -c "from app.database.core import DatabaseCore; DatabaseCore().get_connection().close(); print('Schema Initialized')"

# --- 3. Start Application ---
echo "[Entrypoint] Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
