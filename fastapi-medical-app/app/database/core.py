import sqlite3
import os
import re

DB_PATH = os.getenv("DB_PATH", "app/database/medical.db")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class DatabaseCore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = dict_factory
        return conn

    def _ensure_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 0. Ensure Base Tables Exist
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
            # Ensure FTS Table
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS drugs_fts USING fts5(ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)")

            # 1. Main Drugs Table Updates
            self._migrate_drugs_table(cursor)

            # 2. Drug Staging Table
            self._migrate_staging_table(cursor)

            # 3. Drug History Table
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
            
            # 4. Drug Staging History
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
                    action TEXT, -- 'rejected', 'cleared', 'approved'
                    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    archived_by TEXT
                )
            """)

            # 5. Drug Disease Links & Migration
            self._migrate_drug_disease_links(cursor)

            # 6. Raw Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT,
                    raw_content TEXT,
                    source_ip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. Knowledge Base
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drug_name_norm TEXT,
                    disease_name_norm TEXT,
                    raw_drug_name TEXT,
                    raw_disease_name TEXT,
                    treatment_type TEXT, 
                    disease_icd TEXT,
                    source_id TEXT, 
                    confidence_score REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_lookup ON knowledge_base(drug_name_norm, disease_name_norm)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_type ON knowledge_base(treatment_type)")
                
            conn.commit()
        except sqlite3.Error as e:
            print(f"DB Init Error: {e}")
        finally:
            conn.close()

    def _migrate_drugs_table(self, cursor):
        cursor.execute("PRAGMA table_info(drugs)")
        columns = [info['name'] for info in cursor.fetchall()]
        
        updates = [
            ('tu_dong_nghia', 'TEXT'),
            ('created_at', 'TIMESTAMP'),
            ('created_by', 'TEXT'),
            ('updated_at', 'TIMESTAMP'),
            ('updated_by', 'TEXT'),
            ('classification', 'TEXT'),
            ('note', 'TEXT')
        ]
        
        for col, dtype in updates:
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE drugs ADD COLUMN {col} {dtype}")
                except Exception:
                    pass

    def _migrate_staging_table(self, cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drug_staging (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        cursor.execute("PRAGMA table_info(drug_staging)")
        current_staging_cols = [info['name'] for info in cursor.fetchall()]
        if 'classification' not in current_staging_cols:
            cursor.execute("ALTER TABLE drug_staging ADD COLUMN classification TEXT")
        if 'note' not in current_staging_cols:
            cursor.execute("ALTER TABLE drug_staging ADD COLUMN note TEXT")

    def _migrate_drug_disease_links(self, cursor):
        # Create Table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drug_disease_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        cursor.execute("PRAGMA table_info(drug_disease_links)")
        link_columns = [info['name'] for info in cursor.fetchall()]

        # ID Column Upgrade Check
        if 'id' not in link_columns:
            print("Migrating drug_disease_links to include ID column...")
            try:
                cursor.execute("ALTER TABLE drug_disease_links RENAME TO drug_disease_links_old")
                cursor.execute("""
                    CREATE TABLE drug_disease_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                cursor.execute("""
                    INSERT INTO drug_disease_links (sdk, icd_code, treatment_note, is_verified)
                    SELECT sdk, icd_code, treatment_note, is_verified FROM drug_disease_links_old
                """)
                cursor.execute("DROP TABLE drug_disease_links_old")
                
                cursor.execute("PRAGMA table_info(drug_disease_links)")
                link_columns = [info['name'] for info in cursor.fetchall()]
            except sqlite3.Error as e:
                print(f"Migration Failed: {e}")
                raise e

        # Column Checks
        updates = [
            ('coverage_type', 'TEXT'),
            ('created_by', 'TEXT'),
            ('status', "TEXT DEFAULT 'active'"),
            ('sdk', 'TEXT'),
            ('icd_code', 'TEXT')
        ]
        
        for col, dtype in updates:
            if col not in link_columns:
                try:
                    cursor.execute(f"ALTER TABLE drug_disease_links ADD COLUMN {col} {dtype}")
                except Exception:
                    pass
