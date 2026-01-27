import sqlite3
import os
import time
import gc
import psycopg2
from psycopg2.extras import RealDictCursor

DB_PATH = os.getenv("DB_PATH", "app/database/medical.db")
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

# Postgres Config
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
PG_DB = os.getenv("POSTGRES_DB", "medical_db")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class DatabaseCore:
    def __init__(self, db_path=DB_PATH):
        self.db_type = DB_TYPE
        self.db_path = db_path # Kept for SQLite fallback
        
        print(f"[DB Core] Initializing Database Mode: {self.db_type.upper()}")

        if self.db_type == 'postgres':
            self._init_postgres()
        else:
            self._init_sqlite()

    def _init_postgres(self):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self._ensure_tables_postgres()
                print(f"[DB Core] Postgres Init successful on attempt {attempt+1}")
                break
            except Exception as e:
                print(f"[DB Core Warning] Postgres Init failed (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2)
        else:
            print("[DB Core ERROR] FATAL: Could not initialize Postgres DB.")
            raise RuntimeError("Postgres DB Init Failed")

    def _init_sqlite(self):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self._ensure_tables_sqlite()
                print(f"[DB Core] SQLite Init successful on attempt {attempt+1}")
                break
            except Exception as e:
                print(f"[DB Core Warning] SQLite Init failed (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(2)
        else:
            print("[DB Core ERROR] FATAL: Could not initialize SQLite DB.")
            raise RuntimeError("SQLite Database Init Failed")

    class PostgresCursorWrapper:
        """
        Wraps psycopg2 cursor to support SQLite-style '?' placeholders
        by converting them to '%s' on the fly.
        """
        def __init__(self, cursor):
            self.cursor = cursor

        def execute(self, query, vars=None):
            # Simple replace '?' -> '%s'
            # Note: This is a naive replacement. It might break if '?' is inside a string literal.
            # But for our API params usage it covers 99% of cases.
            if query and '?' in query:
                query = query.replace('?', '%s')
            return self.cursor.execute(query, vars)

        def executemany(self, query, vars_list):
            if query and '?' in query:
                query = query.replace('?', '%s')
            return self.cursor.executemany(query, vars_list)

        def fetchone(self):
            return self.cursor.fetchone()

        def fetchall(self):
            return self.cursor.fetchall()

        def __iter__(self):
            return iter(self.cursor)
            
        @property
        def description(self):
            return self.cursor.description
            
        @property
        def rowcount(self):
            return self.cursor.rowcount
            
        @property
        def lastrowid(self):
            # Postgres doesn't support lastrowid standardly.
            # We implemented logic in services to use RETURNING or ignore it.
            return self.cursor.lastrowid
            
        def close(self):
            self.cursor.close()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    class PostgresConnectionWrapper:
        def __init__(self, conn):
            self.conn = conn

        def cursor(self):
            return DatabaseCore.PostgresCursorWrapper(self.conn.cursor())

        def commit(self):
            self.conn.commit()
            
        def rollback(self):
            self.conn.rollback()

        def close(self):
            self.conn.close()
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

        # Proxy other attrs
        def __getattr__(self, name):
            return getattr(self.conn, name)

    def get_connection(self):
        if self.db_type == 'postgres':
            # Postgres Connection
            try:
                conn = psycopg2.connect(
                    user=PG_USER,
                    password=PG_PASSWORD,
                    dbname=PG_DB,
                    host=PG_HOST,
                    port=PG_PORT,
                    cursor_factory=RealDictCursor
                )
                conn.autocommit = False 
                # Wrap it!
                return self.PostgresConnectionWrapper(conn)
            except Exception as e:
                print(f"[DB Connection Error] {e}")
                raise
        else:
            # SQLite Connection
            for attempt in range(5):
                try:
                    gc.collect() 
                    conn = sqlite3.connect(self.db_path, timeout=60.0)
                    conn.execute("PRAGMA journal_mode=DELETE;")
                    conn.row_factory = dict_factory
                    return conn
                except Exception:
                    time.sleep(1)
            
            conn = sqlite3.connect(self.db_path, timeout=60.0)
            conn.execute("PRAGMA journal_mode=DELETE;")
            conn.row_factory = dict_factory
            return conn

    # =========================================================================
    # POSTGRES SCHEMAS
    # =========================================================================
    def _ensure_tables_postgres(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # 0. Base Drugs Table
                # Postgres: SERIAL for AI, TIMESTAMP without time zone
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS drugs (
                        id SERIAL PRIMARY KEY,
                        ten_thuoc TEXT,
                        hoat_chat TEXT,
                        cong_ty_san_xuat TEXT,
                        so_dang_ky TEXT,
                        chi_dinh TEXT,
                        tu_dong_nghia TEXT,
                        is_verified INTEGER DEFAULT 0,
                        search_text TEXT,
                        created_at TIMESTAMP,
                        created_by TEXT,
                        updated_at TIMESTAMP,
                        updated_by TEXT,
                        classification TEXT,
                        note TEXT,
                        search_vector TSVECTOR
                    )
                """)
                # GIN Index for FTS
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_search_vector ON drugs USING GIN(search_vector)")
                
                # Trigger to update search_vector (simple concatenation of fields)
                # Note: Using 'simple' config or 'vietnamese' if available, defaulting to 'simple' for wide compat
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION drugs_trigger_update() RETURNS trigger AS $$
                    BEGIN
                        NEW.search_vector := 
                            setweight(to_tsvector('simple', COALESCE(NEW.ten_thuoc, '')), 'A') ||
                            setweight(to_tsvector('simple', COALESCE(NEW.hoat_chat, '')), 'B') ||
                            setweight(to_tsvector('simple', COALESCE(NEW.cong_ty_san_xuat, '')), 'C') ||
                            setweight(to_tsvector('simple', COALESCE(NEW.search_text, '')), 'D');
                        RETURN NEW;
                    END
                    $$ LANGUAGE plpgsql;
                """)
                cursor.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'drugs_update_trigger') THEN
                            CREATE TRIGGER drugs_update_trigger
                            BEFORE INSERT OR UPDATE ON drugs
                            FOR EACH ROW EXECUTE FUNCTION drugs_trigger_update();
                        END IF;
                    END
                    $$;
                """)

                # 0b. Diseases Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS diseases (
                        id TEXT PRIMARY KEY,
                        icd_code TEXT UNIQUE,
                        disease_name TEXT,
                        chapter_name TEXT,
                        slug TEXT,
                        search_text TEXT,
                        is_active TEXT DEFAULT 'active',
                        search_vector TSVECTOR
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_diseases_icd ON diseases(icd_code)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_diseases_search_vector ON diseases USING GIN(search_vector)")
                
                # Diseases Trigger
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION diseases_trigger_update() RETURNS trigger AS $$
                    BEGIN
                        NEW.search_vector := 
                            setweight(to_tsvector('simple', COALESCE(NEW.icd_code, '')), 'A') ||
                            setweight(to_tsvector('simple', COALESCE(NEW.disease_name, '')), 'B') ||
                            setweight(to_tsvector('simple', COALESCE(NEW.search_text, '')), 'C');
                        RETURN NEW;
                    END
                    $$ LANGUAGE plpgsql;
                """)
                cursor.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'diseases_update_trigger') THEN
                            CREATE TRIGGER diseases_update_trigger
                            BEFORE INSERT OR UPDATE ON diseases
                            FOR EACH ROW EXECUTE FUNCTION diseases_trigger_update();
                        END IF;
                    END
                    $$;
                """)

                # 2. Drug Staging Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS drug_staging (
                        id SERIAL PRIMARY KEY,
                        ten_thuoc TEXT NOT NULL,
                        hoat_chat TEXT,
                        cong_ty_san_xuat TEXT,
                        so_dang_ky TEXT,
                        chi_dinh TEXT,
                        tu_dong_nghia TEXT,
                        search_text TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT,
                        conflict_type TEXT,
                        conflict_id INTEGER,
                        classification TEXT,
                        note TEXT
                    )
                """)

                # 3. Drug History Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS drug_history (
                        id SERIAL PRIMARY KEY,
                        original_drug_id INTEGER,
                        ten_thuoc TEXT,
                        hoat_chat TEXT,
                        cong_ty_san_xuat TEXT,
                        so_dang_ky TEXT,
                        chi_dinh TEXT,
                        tu_dong_nghia TEXT,
                        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        archived_by TEXT
                    )
                """)
                
                # 4. Drug Staging History
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS drug_staging_history (
                        id SERIAL PRIMARY KEY,
                        original_staging_id INTEGER,
                        ten_thuoc TEXT,
                        hoat_chat TEXT,
                        cong_ty_san_xuat TEXT,
                        so_dang_ky TEXT,
                        chi_dinh TEXT,
                        tu_dong_nghia TEXT,
                        action TEXT, 
                        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        archived_by TEXT
                    )
                """)

                # 5. Drug Disease Links
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS drug_disease_links (
                        id SERIAL PRIMARY KEY,
                        drug_id INTEGER,
                        disease_id INTEGER,
                        sdk TEXT,
                        icd_code TEXT,
                        treatment_note TEXT,
                        is_verified INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        coverage_type TEXT,
                        created_by TEXT,
                        status TEXT DEFAULT 'active'
                    )
                """)

                # 6. Logs (Raw & API)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS raw_logs (
                        id SERIAL PRIMARY KEY,
                        batch_id TEXT,
                        raw_content TEXT,
                        source_ip TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_logs (
                        id SERIAL PRIMARY KEY,
                        endpoint TEXT,
                        method TEXT,
                        status_code INTEGER,
                        response_time_ms REAL,
                        client_ip TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint, created_at)")

                # 7. Knowledge Base
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_base (
                        id SERIAL PRIMARY KEY,
                        
                        drug_name TEXT,
                        drug_name_norm TEXT,
                        drug_ref_id INTEGER,
                        
                        disease_icd TEXT,
                        disease_name TEXT,
                        disease_name_norm TEXT,
                        disease_ref_id INTEGER,
                        
                        secondary_disease_icd TEXT,
                        secondary_disease_name TEXT,
                        secondary_disease_name_norm TEXT,
                        secondary_disease_ref_id INTEGER,
                        
                        treatment_type TEXT,
                        tdv_feedback TEXT,
                        symptom TEXT,
                        prescription_reason TEXT,
                        
                        frequency INTEGER DEFAULT 1,
                        confidence_score REAL DEFAULT 0.0,
                        batch_id TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_lookup ON knowledge_base(drug_name_norm, disease_name_norm)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_type ON knowledge_base(treatment_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_icd ON knowledge_base(disease_icd)")

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # =========================================================================
    # SQLITE SCHEMAS (LEGACY)
    # =========================================================================
    def _ensure_tables_sqlite(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 0. Base Tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ten_thuoc TEXT,
                    hoat_chat TEXT,
                    cong_ty_san_xuat TEXT,
                    so_dang_ky TEXT,
                    chi_dinh TEXT,
                    tu_dong_nghia TEXT,
                    is_verified INTEGER DEFAULT 0,
                    search_text TEXT,
                    created_at TIMESTAMP,
                    created_by TEXT,
                    updated_at TIMESTAMP,
                    updated_by TEXT,
                    classification TEXT,
                    note TEXT
                )
            """)
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS drugs_fts USING fts5(ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diseases (
                    id TEXT PRIMARY KEY,
                    icd_code TEXT UNIQUE,
                    disease_name TEXT,
                    chapter_name TEXT,
                    slug TEXT,
                    search_text TEXT,
                    is_active TEXT DEFAULT 'active'
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_diseases_icd ON diseases(icd_code)")
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS diseases_fts USING fts5(icd_code, disease_name, search_text)")

            self._migrate_drugs_table(cursor)
            self._migrate_staging_table(cursor)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drug_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_drug_id INTEGER,
                    ten_thuoc TEXT,
                    hoat_chat TEXT,
                    cong_ty_san_xuat TEXT,
                    so_dang_ky TEXT,
                    chi_dinh TEXT,
                    tu_dong_nghia TEXT,
                    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    archived_by TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drug_staging_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_staging_id INTEGER,
                    ten_thuoc TEXT,
                    hoat_chat TEXT,
                    cong_ty_san_xuat TEXT,
                    so_dang_ky TEXT,
                    chi_dinh TEXT,
                    tu_dong_nghia TEXT,
                    action TEXT, 
                    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    archived_by TEXT
                )
            """)

            self._migrate_drug_disease_links(cursor)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT,
                    raw_content TEXT,
                    source_ip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT,
                    method TEXT,
                    status_code INTEGER,
                    response_time_ms REAL,
                    client_ip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint, created_at)")


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drug_name TEXT,
                    drug_name_norm TEXT,
                    drug_ref_id INTEGER,
                    disease_icd TEXT,
                    disease_name TEXT,
                    disease_name_norm TEXT,
                    disease_ref_id INTEGER,
                    secondary_disease_icd TEXT,
                    secondary_disease_name TEXT,
                    secondary_disease_name_norm TEXT,
                    secondary_disease_ref_id INTEGER,
                    treatment_type TEXT,                
                    tdv_feedback TEXT,                  
                    symptom TEXT,
                    prescription_reason TEXT,
                    frequency INTEGER DEFAULT 1,
                    confidence_score REAL DEFAULT 0.0,
                    batch_id TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_lookup ON knowledge_base(drug_name_norm, disease_name_norm)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_type ON knowledge_base(treatment_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_icd ON knowledge_base(disease_icd)")
            
            self._migrate_kb_table(cursor)
                
            conn.commit()
        except sqlite3.Error as e:
            print(f"DB Init Error: {e}")
            raise 
        finally:
            conn.close()

    def _migrate_drugs_table(self, cursor):
        cursor.execute("PRAGMA table_info(drugs)")
        columns = [info['name'] for info in cursor.fetchall()]
        updates = [('tu_dong_nghia', 'TEXT'), ('created_at', 'TIMESTAMP'), ('created_by', 'TEXT'), ('updated_at', 'TIMESTAMP'), ('updated_by', 'TEXT'), ('classification', 'TEXT'), ('note', 'TEXT')]
        for col, dtype in updates:
            if col not in columns:
                try: cursor.execute(f"ALTER TABLE drugs ADD COLUMN {col} {dtype}")
                except Exception: pass

    def _migrate_staging_table(self, cursor):
        cursor.execute("CREATE TABLE IF NOT EXISTS drug_staging (id INTEGER PRIMARY KEY AUTOINCREMENT, ten_thuoc TEXT NOT NULL)") # Basic
        # Check cols and add
        cursor.execute("PRAGMA table_info(drug_staging)")
        cols = {info['name'] for info in cursor.fetchall()}
        required = {'hoat_chat': 'TEXT', 'cong_ty_san_xuat': 'TEXT', 'so_dang_ky': 'TEXT', 'chi_dinh': 'TEXT', 'tu_dong_nghia': 'TEXT', 'search_text': 'TEXT', 'status': "TEXT DEFAULT 'pending'", 'created_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", 'created_by': 'TEXT', 'conflict_type': 'TEXT', 'conflict_id': 'INTEGER', 'classification': 'TEXT', 'note': 'TEXT'}
        for col, dtype in required.items():
            if col not in cols:
                try: cursor.execute(f"ALTER TABLE drug_staging ADD COLUMN {col} {dtype}")
                except Exception: pass

    def _migrate_drug_disease_links(self, cursor):
        cursor.execute("CREATE TABLE IF NOT EXISTS drug_disease_links (id INTEGER PRIMARY KEY AUTOINCREMENT, drug_id INTEGER, disease_id INTEGER)")
        cursor.execute("PRAGMA table_info(drug_disease_links)")
        cols = {info['name'] for info in cursor.fetchall()}
        required = {'sdk': 'TEXT', 'icd_code': 'TEXT', 'treatment_note': 'TEXT', 'is_verified': 'INTEGER DEFAULT 0', 'created_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", 'coverage_type': 'TEXT', 'created_by': 'TEXT', 'status': "TEXT DEFAULT 'active'"}
        for col, dtype in required.items():
            if col not in cols:
                try: cursor.execute(f"ALTER TABLE drug_disease_links ADD COLUMN {col} {dtype}")
                except Exception: pass

    def _migrate_kb_table(self, cursor):
        cursor.execute("PRAGMA table_info(knowledge_base)")
        cols = {info['name'] for info in cursor.fetchall()}
        required = {"drug_name": "TEXT", "drug_name_norm": "TEXT", "drug_ref_id": "INTEGER", "disease_icd": "TEXT", "disease_name": "TEXT", "disease_name_norm": "TEXT", "disease_ref_id": "INTEGER", "secondary_disease_icd": "TEXT", "secondary_disease_name": "TEXT", "secondary_disease_name_norm": "TEXT", "secondary_disease_ref_id": "INTEGER", "tdv_feedback": "TEXT", "symptom": "TEXT", "prescription_reason": "TEXT", "batch_id": "TEXT"}
        for col, dtype in required.items():
            if col not in cols:
                try: cursor.execute(f"ALTER TABLE knowledge_base ADD COLUMN {col} {dtype}")
                except Exception: pass
