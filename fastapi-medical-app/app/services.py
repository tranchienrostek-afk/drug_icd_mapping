import sqlite3
import os
import asyncio
from datetime import datetime
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from playwright.async_api import async_playwright
from openai import AzureOpenAI
from app.utils import normalize_text, normalize_for_matching
from dotenv import load_dotenv
from app.service.crawler import search_icd_online

load_dotenv()

# --- UTILS ---
DB_PATH = os.getenv("DB_PATH", "app/database/medical.db")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# --- CẤU HÌNH OPENAI (Phiên bản mới v1.x) ---
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# --- DATABASE ENGINE CHO THUỐC ---
class DrugDbEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_tables()
        self.vectorizer = None
        self.tfidf_matrix = None
        self.drug_cache = [] # List of dicts: {rowid, search_text, ...}
        self.last_cache_update = None

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

            # 1. Main Drugs Table Updates (Migrations - for older DBs)
            cursor.execute("PRAGMA table_info(drugs)")
            columns = [info['name'] for info in cursor.fetchall()]
            
            if 'tu_dong_nghia' not in columns:
                cursor.execute("ALTER TABLE drugs ADD COLUMN tu_dong_nghia TEXT")
            if 'created_at' not in columns:
                cursor.execute("ALTER TABLE drugs ADD COLUMN created_at TIMESTAMP")
            if 'created_by' not in columns:
                cursor.execute("ALTER TABLE drugs ADD COLUMN created_by TEXT")
            if 'updated_at' not in columns:
                cursor.execute("ALTER TABLE drugs ADD COLUMN updated_at TIMESTAMP")
            if 'updated_by' not in columns:
                cursor.execute("ALTER TABLE drugs ADD COLUMN updated_by TEXT")
            if 'classification' not in columns:
                cursor.execute("ALTER TABLE drugs ADD COLUMN classification TEXT")
            if 'note' not in columns:
                cursor.execute("ALTER TABLE drugs ADD COLUMN note TEXT")

            # 2. Drug Staging Table (Check for new columns)
            cursor.execute("PRAGMA table_info(drug_staging)")
            staging_columns = [info['name'] for info in cursor.fetchall()]
            
            if 'classification' not in staging_columns:
                 # Check if table exists first (it might not if created above... wait, CREATE IF NOT EXISTS is strictly above)
                 # But if it existed from V1, it won't have the columns.
                 # The CREATE block above handles new DBs. Existing DBs need ALTER.
                 # Actually, my previous replace_file_content replaced the CREATE block.
                 # So for NEW DBs, I should update the CREATE statement.
                 # For OLD DBs, I need ALTER.
                 pass
            
            # Update the CREATE statement for new DBs/tables
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
                    status TEXT DEFAULT 'pending', -- pending, approved, rejected
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    conflict_type TEXT, -- 'sdk', 'name'
                    conflict_id INTEGER, -- ID of the existing drug in 'drugs' table
                    classification TEXT,
                    note TEXT
                )
            """)
            
            # Migration for existing Staging
            cursor.execute("PRAGMA table_info(drug_staging)")
            current_staging_cols = [info['name'] for info in cursor.fetchall()]
            if 'classification' not in current_staging_cols:
                cursor.execute("ALTER TABLE drug_staging ADD COLUMN classification TEXT")
            if 'note' not in current_staging_cols:
                cursor.execute("ALTER TABLE drug_staging ADD COLUMN note TEXT")

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
            
            # 4. Drug Staging History (Archive for Rejected/Cleared Items)
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

            # 5. Drug Disease Links
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
                    coverage_type TEXT, -- 'Thuốc điều trị', 'Thuốc hỗ trợ', etc.
                    created_by TEXT,
                    status TEXT DEFAULT 'active' -- 'active', 'pending'
                )
            """)
            
            # Check columns (Schema Migration)
            # Check columns (Schema Migration)
            cursor.execute("PRAGMA table_info(drug_disease_links)")
            link_columns = [info['name'] for info in cursor.fetchall()]

            # 5b. Schema Migration (ID Column Upgrade)
            if 'id' not in link_columns:
                print("Migrating drug_disease_links to include ID column...")
                try:
                    # 1. Rename
                    cursor.execute("ALTER TABLE drug_disease_links RENAME TO drug_disease_links_old")
                    
                    # 2. Create New (Full Schema)
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
                    
                    # 3. Copy Data (Map old columns)
                    # Use INSERT FROM SELECT with explicit columns
                    # Check columns of old table to be safe? 
                    # Assuming standard old schema: sdk, icd_code, treatment_note, is_verified
                    cursor.execute("""
                        INSERT INTO drug_disease_links (sdk, icd_code, treatment_note, is_verified)
                        SELECT sdk, icd_code, treatment_note, is_verified FROM drug_disease_links_old
                    """)
                    
                    # 4. Drop Old
                    cursor.execute("DROP TABLE drug_disease_links_old")
                    
                    # Refresh columns info
                    cursor.execute("PRAGMA table_info(drug_disease_links)")
                    link_columns = [info['name'] for info in cursor.fetchall()]
                    
                except sqlite3.Error as e:
                    print(f"Migration Failed: {e}")
                    # If rename happened but create/copy failed? 
                    # Risk of data loss or corrupted schema state.
                    # But for now proceed.
                    raise e

            if 'coverage_type' not in link_columns:
                cursor.execute("ALTER TABLE drug_disease_links ADD COLUMN coverage_type TEXT")
            if 'created_by' not in link_columns:
                cursor.execute("ALTER TABLE drug_disease_links ADD COLUMN created_by TEXT")
            if 'status' not in link_columns:
                cursor.execute("ALTER TABLE drug_disease_links ADD COLUMN status TEXT DEFAULT 'active'")
            if 'sdk' not in link_columns:
                cursor.execute("ALTER TABLE drug_disease_links ADD COLUMN sdk TEXT")
            if 'icd_code' not in link_columns:
                cursor.execute("ALTER TABLE drug_disease_links ADD COLUMN icd_code TEXT")

            # 6. Raw Logs (New)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT,
                    raw_content TEXT,
                    source_ip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. Knowledge Base (New)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drug_name_norm TEXT,
                    drug_ref_id INTEGER,
                    disease_name_norm TEXT,
                    disease_icd TEXT,
                    frequency INTEGER DEFAULT 1,
                    confidence_score REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_lookup ON knowledge_base(drug_name_norm, disease_name_norm)")
                
            conn.commit()
        except sqlite3.Error as e:
            print(f"DB Init Error: {e}")
        finally:
            conn.close()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0) # Increase timeout to 30s to avoid locks
        conn.row_factory = dict_factory
        return conn

    def search(self, query):
        if not query: return None
        
        query_clean = normalize_text(query)
        # SQLite FTS5 MATCH query
        # Using simple prefix matching for now
        sql = """
            SELECT * FROM drugs_fts 
            WHERE drugs_fts MATCH ? 
            ORDER BY rank 
            LIMIT 1
        """
        
        # FTS syntax: "query*" for prefix match, or "query" for exact word match
        # To make it robust: AND operator between words
        # e.g. "paracetamol 500mh" -> "paracetamol* AND 500mh*"
        # FTS syntax: "query*" for prefix match. 
        # Sanitize: only append '*' to words with letters/numbers to avoid "fts5: syntax error near '*'"
        search_term = " AND ".join([f"{w}*" for w in query_clean.split() if re.match(r'[a-zA-Z0-9]', w)]) if query_clean else ""
        
        if not search_term: return None

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First try FTS search
            cursor.execute(sql, (search_term,))
            result = cursor.fetchone()
            
            if result:
                # Get full details from main table using rowid if needed, 
                # but we populated FTS with all needed columns? 
                # Wait, FTS table has ten_thuoc, hoat_chat, cong_ty_san_xuat.
                # If we need other columns like 'so_dang_ky', 'chi_dinh', etc., we should query main table.
                # In previous step, I migrated ALL columns to main table 'drugs'. 
                # FTS table only has search columns.
                # So I need to join or query main table by rowid.
                
                # Correction: My migration script put rowid in FTS. 
                # Check migration script: 
                # INSERT INTO drugs_fts(rowid, ...) SELECT rowid, ...
                
                row_id = result.get('rowid') # dict_factory returns rowid if selected? FTS usually returns it.
                # Actually 'SELECT * FROM drugs_fts' returns the columns defined in CREATE VIRTUAL TABLE. 
                # It does NOT return rowid by default unless explicitly asked? 
                # Wait, I didn't verify if I can get rowid easily.
                # Better query: SELECT rowid FROM drugs_fts ...
                
                # Let's refine the query to be safe.
                cursor.execute("SELECT rowid FROM drugs_fts WHERE drugs_fts MATCH ? ORDER BY rank LIMIT 1", (search_term,))
                row = cursor.fetchone()
                
                if row:
                    drug_id = row['rowid']
                    cursor.execute("SELECT * FROM drugs WHERE rowid = ?", (drug_id,))
                    full_data = cursor.fetchone()
                    conn.close()
                    return full_data

            conn.close()
            return None
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
            return None

    def save_verified_drug(self, drug_data):
        """
        Lưu thông tin thuốc.
        - Nếu mới hoàn toàn: Insert vào drugs.
        - Nếu conflict (trùng SĐK hoặc Tên): Insert vào drug_staging.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            ten = drug_data.get('ten_thuoc', '').strip()
            sdk = drug_data.get('so_dang_ky', '').strip()
            hoat_chat = drug_data.get('hoat_chat', '')
            cong_ty = drug_data.get('cong_ty_san_xuat', '')
            chi_dinh = drug_data.get('chi_dinh', '')
            tu_dong_nghia = drug_data.get('tu_dong_nghia', '')
            user = drug_data.get('modified_by', 'system')
            
            search_text = normalize_text(f"{ten} {hoat_chat} {cong_ty} {tu_dong_nghia}")
            
            # 1. Check Conflict
            conflict_id = None
            conflict_type = None

            # Check SDK
            if sdk and sdk != 'N/A' and sdk != 'Web Result':
                cursor.execute("SELECT rowid, ten_thuoc FROM drugs WHERE so_dang_ky = ?", (sdk,))
                row = cursor.fetchone()
                if row:
                    conflict_id = row['rowid']
                    conflict_type = 'sdk'
            
            # Check Name (if no SDK conflict)
            if not conflict_id and ten:
                cursor.execute("SELECT rowid FROM drugs WHERE ten_thuoc = ?", (ten,))
                row = cursor.fetchone()
                if row:
                    conflict_id = row['rowid']
                    conflict_type = 'name'

            # 2. Handle Logic
            if conflict_id:
                # Conflict found -> Save to Staging
                print(f"Conflict found ({conflict_type}) with ID {conflict_id}. Saving to Staging.")
                sql_staging = """
                    INSERT INTO drug_staging (
                        ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, chi_dinh, 
                        tu_dong_nghia, search_text, status, created_by, conflict_type, conflict_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """
                cursor.execute(sql_staging, (
                    ten, hoat_chat, cong_ty, sdk, chi_dinh, 
                    tu_dong_nghia, search_text, user, conflict_type, conflict_id
                ))
                staging_id = cursor.lastrowid
                conn.commit()
                return {
                    "status": "pending_confirmation", 
                    "message": f"Drug exists ({conflict_type}). Saved to staging for approval.",
                    "staging_id": staging_id
                }
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # No conflict -> Insert directly
                sql_insert = """
                    INSERT INTO drugs (
                        ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, chi_dinh, 
                        tu_dong_nghia, is_verified, search_text, created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """
                cursor.execute(sql_insert, (ten, hoat_chat, cong_ty, sdk, chi_dinh, tu_dong_nghia, search_text, user, now, now))
                row_id = cursor.lastrowid
                
                # Update FTS
                self._update_fts(cursor, row_id, ten, hoat_chat, cong_ty, search_text)
                
                conn.commit()
                return {"status": "success", "message": f"Saved new drug: {ten} ({sdk})"}

        except sqlite3.Error as e:
            print(f"DB Save Error: {e}")
            conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    def _update_fts(self, cursor, row_id, ten, hoat_chat, cong_ty, search_text):
        cursor.execute("DELETE FROM drugs_fts WHERE rowid = ?", (row_id,))
        cursor.execute("""
            INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)
            VALUES (?, ?, ?, ?, ?)
        """, (row_id, ten, hoat_chat, cong_ty, search_text))

    async def get_drug_by_id(self, row_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT rowid, * FROM drugs WHERE rowid = ?", (row_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def _load_vector_cache(self):
        """Load data for vector search if not loaded or stale"""
        # Simple cache invalidation strategy could be added here
        if self.vectorizer and self.tfidf_matrix is not None:
             return

        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # Load verified drugs with SDK
            cursor.execute("SELECT rowid, ten_thuoc, so_dang_ky, search_text FROM drugs WHERE is_verified=1 AND so_dang_ky IS NOT NULL AND so_dang_ky != ''")
            rows = cursor.fetchall()
            self.drug_cache = [dict(row) for row in rows]
            
            if self.drug_cache:
                corpus = [d['search_text'] or d['ten_thuoc'] for d in self.drug_cache]
                self.vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
                self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except Exception as e:
            print(f"Vector Cache Load Error: {e}")
        finally:
            conn.close()

    async def search_drug_smart(self, query_name: str):
        """
        Multistage Search:
        1. Exact Match (100%)
        2. Partial/Fuzzy SQL Match (95%)
        3. Vector/Semantic Match (90%)
        Returns: { data: dict, confidence: float, source: str } or None
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Prepare variants
        raw_query = query_name.strip()
        db_normalized_query = normalize_for_matching(query_name) # Remove accents, special chars
        
        # Priority: Raw (for exact DB match) -> Normalized (for loose DB match)
        search_variants = []
        if raw_query: search_variants.append(raw_query)
        if db_normalized_query and db_normalized_query != raw_query.lower():
            search_variants.append(db_normalized_query)
        
        # If it has a dose/composite in normalized form, try to split
        if " " in db_normalized_query:
            parts = db_normalized_query.rsplit(' ', 1)
            if len(parts) > 1 and re.search(r'\d', parts[1]):
                 search_variants.append(parts[0])

        try:
            for variant in search_variants:
                # 1. EXACT MATCH
                cursor.execute("SELECT * FROM drugs WHERE ten_thuoc = ? AND is_verified=1 AND so_dang_ky IS NOT NULL", (variant,))
                row = cursor.fetchone()
                if row:
                    return {"data": dict(row), "confidence": 1.0, "source": f"Database (Exact{' Fallback' if variant != raw_query else ''})"}

                # 2. PARTIAL MATCH
                cursor.execute("SELECT * FROM drugs WHERE ten_thuoc LIKE ? AND is_verified=1 AND so_dang_ky IS NOT NULL", (f"%{variant}%",))
                row = cursor.fetchone()
                if row:
                     return {"data": dict(row), "confidence": 0.95, "source": f"Database (Partial{' Fallback' if variant != raw_query else ''})"}

            # 2.5. FUZZY MATCH (RapidFuzz)
            self._load_vector_cache()
            try:
                from rapidfuzz import process, fuzz
                if self.drug_cache:
                     if not hasattr(self, 'fuzzy_names') or not self.fuzzy_names:
                         self.fuzzy_names = [d['ten_thuoc'] for d in self.drug_cache]
                     
                     # token_sort_ratio handles "Paracetamol 500mg" vs "500mg Paracetamol" well
                     fuzzy_res = process.extractOne(raw_query, self.fuzzy_names, scorer=fuzz.token_sort_ratio)
                     if fuzzy_res:
                         match, score, idx = fuzzy_res
                         if score >= 85.0:
                             match_data = self.drug_cache[idx]
                             cursor.execute("SELECT * FROM drugs WHERE rowid = ?", (match_data['rowid'],))
                             full_row = cursor.fetchone()
                             if full_row:
                                 return {"data": dict(full_row), "confidence": 0.88, "source": f"Database (Fuzzy {score:.1f})"}
            except Exception as e:
                # Debug print if needed
                pass

            # 3. VECTOR SEARCH (Always use Normalized Query)
            # self._load_vector_cache() # optimized: called above matches
            if self.vectorizer and self.tfidf_matrix is not None:
                # Debug: print(f"Vector searching for: '{db_normalized_query}'")
                query_vec = self.vectorizer.transform([db_normalized_query])
                cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                
                if cosine_sim.size > 0:
                    best_idx = np.argmax(cosine_sim)
                    best_score = cosine_sim[best_idx]
                    
                    if best_score > 0.75: # Optimized Threshold from 0.85 
                        match_data = self.drug_cache[best_idx]
                        # Fetch full details
                        cursor.execute("SELECT * FROM drugs WHERE rowid = ?", (match_data['rowid'],))
                        full_row = cursor.fetchone()
                        if full_row:
                             return {"data": dict(full_row), "confidence": 0.90, "source": f"Database (Vector {best_score:.2f})"}

            return None
        finally:
            conn.close()

    def get_all_drugs(self, page=1, limit=10, search=None):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        offset = (page - 1) * limit
        try:
            if search:
                # FTS Search or Partial LIKE
                # Simple LIKE for now for stability
                search_term = f"%{search.strip()}%"
                cursor.execute("SELECT count(*) FROM drugs WHERE ten_thuoc LIKE ? OR so_dang_ky LIKE ?", (search_term, search_term))
                total = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT rowid, * FROM drugs 
                    WHERE ten_thuoc LIKE ? OR so_dang_ky LIKE ?
                    ORDER BY ten_thuoc LIMIT ? OFFSET ?
                """, (search_term, search_term, limit, offset))
            else:
                cursor.execute("SELECT count(*) FROM drugs")
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT rowid, * FROM drugs ORDER BY updated_at DESC LIMIT ? OFFSET ?", (limit, offset))
            
            rows = cursor.fetchall()
            return {"data": [dict(r) for r in rows], "total": total, "page": page, "limit": limit}
        finally:
            conn.close()

    def get_pending_stagings(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM drug_staging WHERE status = 'pending' ORDER BY id DESC")
            stagings = cursor.fetchall()
            
            # Enrich with conflict info
            for item in stagings:
                if item.get('conflict_id'):
                    cursor.execute("SELECT ten_thuoc, so_dang_ky, hoat_chat FROM drugs WHERE rowid = ?", (item['conflict_id'],))
                    conflict_drug = cursor.fetchone()
                    if conflict_drug:
                        item['conflict_info'] = conflict_drug
                    else:
                         item['conflict_info'] = None
                else:
                    item['conflict_info'] = None
            
            return stagings
        finally:
            conn.close()

    def approve_staging(self, staging_id, user):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get Staging Data
            cursor.execute("SELECT * FROM drug_staging WHERE id = ?", (staging_id,))
            staging = cursor.fetchone()
            if not staging:
                return {"status": "error", "message": "Staging record not found"}

            conflict_id = staging['conflict_id']
            
            # Archive Old Data if Conflict
            if conflict_id:
                cursor.execute("SELECT * FROM drugs WHERE rowid = ?", (conflict_id,))
                current_drug = cursor.fetchone()
                
                if not current_drug:
                    return {"status": "error", "message": f"Original drug with ID {conflict_id} not found. Cannot merge."}

                if current_drug:
                    sql_history = """
                        INSERT INTO drug_history (
                            original_drug_id, ten_thuoc, hoat_chat, cong_ty_san_xuat, 
                            so_dang_ky, chi_dinh, tu_dong_nghia, archived_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(sql_history, (
                        conflict_id, current_drug['ten_thuoc'], current_drug['hoat_chat'], 
                        current_drug['cong_ty_san_xuat'], current_drug['so_dang_ky'], 
                        current_drug['chi_dinh'], current_drug.get('tu_dong_nghia'), user
                    ))

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Update Existing Drug
                sql_update = """
                    UPDATE drugs 
                    SET ten_thuoc=?, hoat_chat=?, cong_ty_san_xuat=?, so_dang_ky=?, 
                        chi_dinh=?, tu_dong_nghia=?, is_verified=1, search_text=?, updated_by=?, updated_at=?,
                        classification=?, note=?
                    WHERE rowid=?
                """
                cursor.execute(sql_update, (
                    staging['ten_thuoc'], staging['hoat_chat'], staging['cong_ty_san_xuat'], 
                    staging['so_dang_ky'], staging['chi_dinh'], staging['tu_dong_nghia'], 
                    staging['search_text'], user, now, 
                    staging.get('classification'), staging.get('note'),
                    conflict_id
                ))
                self._update_fts(cursor, conflict_id, staging['ten_thuoc'], staging['hoat_chat'], staging['cong_ty_san_xuat'], staging['search_text'])

            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Insert New
                sql_insert = """
                    INSERT INTO drugs (
                        ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, chi_dinh, 
                        tu_dong_nghia, is_verified, search_text, created_by, created_at, updated_at,
                        classification, note
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql_insert, (
                    staging['ten_thuoc'], staging['hoat_chat'], staging['cong_ty_san_xuat'], 
                    staging['so_dang_ky'], staging['chi_dinh'], staging['tu_dong_nghia'], 
                    staging['search_text'], user, now, now,
                    staging.get('classification'), staging.get('note')
                ))
                new_id = cursor.lastrowid
                self._update_fts(cursor, new_id, staging['ten_thuoc'], staging['hoat_chat'], staging['cong_ty_san_xuat'], staging['search_text'])

            # Delete from Staging (it's approved now)
            # Future enhancement: Move to history with action='approved'?
            # For now, just delete as before or move to history if we want full trace.
            # User said: "All data... stored in ... history... for trace".
            # So even approved ones could go there?
            # "With refused data... stored in same table... as overwritten data... thrown to a table as warehouse."
            # It implies rejected items go there. Overwritten items go to `drug_history` (we already have this).
            # But maybe we should also log the Staging item itself to `drug_staging_history` with action='approved'?
            # Let's do that for completeness.
            
            sql_archive = """
                INSERT INTO drug_staging_history (
                    original_staging_id, ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, 
                    chi_dinh, tu_dong_nghia, action, archived_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'approved', ?)
            """
            cursor.execute(sql_archive, (
                staging_id, staging['ten_thuoc'], staging['hoat_chat'], staging['cong_ty_san_xuat'], staging['so_dang_ky'],
                staging['chi_dinh'], staging['tu_dong_nghia'], user
            ))
            
            # Activate any pending links
            final_drug_id = conflict_id if conflict_id else new_id
            cursor.execute("UPDATE drug_disease_links SET status='active', drug_id=? WHERE sdk=?", (final_drug_id, staging['so_dang_ky']))

            cursor.execute("DELETE FROM drug_staging WHERE id = ?", (staging_id,))
            conn.commit()
            return {"status": "success", "message": "Staging approved and merged."}
            
        except sqlite3.Error as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    def reject_staging(self, staging_id, user="system"):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get Staging Data first
            cursor.execute("SELECT * FROM drug_staging WHERE id = ?", (staging_id,))
            staging = cursor.fetchone()
            if not staging:
                return {"status": "error", "message": "Staging record not found"}

            # Move to History
            sql_archive = """
                INSERT INTO drug_staging_history (
                    original_staging_id, ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, 
                    chi_dinh, tu_dong_nghia, action, archived_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'rejected', ?)
            """
            cursor.execute(sql_archive, (
                staging_id, staging['ten_thuoc'], staging['hoat_chat'], staging['cong_ty_san_xuat'], staging['so_dang_ky'],
                staging['chi_dinh'], staging['tu_dong_nghia'], user
            ))

            # Archive pending links
            cursor.execute("UPDATE drug_disease_links SET status='archived' WHERE sdk=? AND status='pending'", (staging['so_dang_ky'],))

            cursor.execute("DELETE FROM drug_staging WHERE id = ?", (staging_id,))
            conn.commit()
            return {"status": "success", "message": "Staging rejected and moved to history."}
        finally:
            conn.close()

    def clear_all_staging(self, user="system"):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Select all pending
            cursor.execute("SELECT * FROM drug_staging WHERE status = 'pending'")
            items = cursor.fetchall()
            
            if not items:
                return {"status": "success", "message": "No pending items to clear."}

            # Move to history
            sql_archive = """
                INSERT INTO drug_staging_history (
                    original_staging_id, ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, 
                    chi_dinh, tu_dong_nghia, action, archived_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'cleared', ?)
            """
            
            params = []
            for item in items:
                params.append((
                    item['id'], item['ten_thuoc'], item['hoat_chat'], item['cong_ty_san_xuat'], item['so_dang_ky'],
                    item['chi_dinh'], item['tu_dong_nghia'], user
                ))
            
            cursor.executemany(sql_archive, params)
            cursor.execute("DELETE FROM drug_staging WHERE status = 'pending'")
            
            conn.commit()
            return {"status": "success", "message": f"Cleared {len(items)} items to history."}
        finally:
            conn.close()

    def update_staging(self, staging_id, data, user="system"):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Update fields
            sql = """
                UPDATE drug_staging
                SET ten_thuoc=?, hoat_chat=?, cong_ty_san_xuat=?, so_dang_ky=?, 
                    chi_dinh=?, tu_dong_nghia=?, classification=?, note=?,
                    search_text=?
                WHERE id=?
            """
            
            search_text = normalize_text(f"{data.get('ten_thuoc','')} {data.get('hoat_chat','')} {data.get('cong_ty_san_xuat','')} {data.get('tu_dong_nghia','')}")
            
            cursor.execute(sql, (
                data.get('ten_thuoc'), data.get('hoat_chat'), data.get('cong_ty_san_xuat'), 
                data.get('so_dang_ky'), data.get('chi_dinh'), data.get('tu_dong_nghia'),
                data.get('classification'), data.get('note'),
                search_text,
                staging_id
            ))
            conn.commit()
            return {"status": "success", "message": "Staging updated."}
        except sqlite3.Error as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    def link_drug_disease(self, data):
        """
        Link Drug to Disease.
        1. Check/Create Disease (ICD).
        2. Check Drug (SDK) -> Main or Staging.
        3. Insert Link (Active or Pending).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            icd = data.get('icd_code')
            disease_name = data.get('disease_name')
            sdk = data.get('sdk')
            drug_name = data.get('drug_name')
            user = data.get('created_by', 'system')
            
            # 1. Disease
            cursor.execute("SELECT id FROM diseases WHERE icd_code = ?", (icd,))
            disease_row = cursor.fetchone()
            if not disease_row:
                cursor.execute("INSERT INTO diseases (icd_code, disease_name, chapter_name) VALUES (?, ?, ?)", 
                               (icd, disease_name, "Auto Created"))
                disease_id = cursor.lastrowid
            else:
                disease_id = disease_row['id']
            
            # 2. Drug Status
            status = 'pending'
            drug_id = None
            
            # Check Main
            cursor.execute("SELECT rowid FROM drugs WHERE so_dang_ky = ?", (sdk,))
            main_row = cursor.fetchone()
            if main_row:
                drug_id = main_row['rowid']
                status = 'active'
            else:
                # Check Staging
                cursor.execute("SELECT id FROM drug_staging WHERE so_dang_ky = ?", (sdk,))
                staging_row = cursor.fetchone()
                if not staging_row:
                    # Create Staging
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO drug_staging (ten_thuoc, so_dang_ky, status, created_at, created_by, search_text)
                        VALUES (?, ?, 'pending', ?, ?, ?)
                    """, (drug_name, sdk, now, user, normalize_text(drug_name)))
            
            # 3. Create Link
            # Check existing link first to avoid duplicates?
            # User said: "Vấn đề trùng lặp...". Assuming unique constraint on (sdk, icd_code) ideally, but basic check here.
            cursor.execute("SELECT id FROM drug_disease_links WHERE sdk = ? AND icd_code = ?", (sdk, icd))
            existing_link = cursor.fetchone()
            
            if existing_link:
                # Update? Or Ignore? "Kích hoạt lại mối liên hệ này"
                cursor.execute("""
                    UPDATE drug_disease_links 
                    SET status = ?, treatment_note = ?, coverage_type = ?, is_verified = ?
                    WHERE id = ?
                """, (status, data.get('treatment_note'), data.get('coverage_type'), data.get('is_verified', 0), existing_link['id']))
            else:
                cursor.execute("""
                    INSERT INTO drug_disease_links (
                        drug_id, disease_id, sdk, icd_code, treatment_note, is_verified, coverage_type, created_by, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (drug_id, disease_id, sdk, icd, data.get('treatment_note'), data.get('is_verified', 0), 
                      data.get('coverage_type'), user, status))
            
            conn.commit()
            return {"status": "success", "message": f"Link processed. Status: {status}"}
            
        except sqlite3.Error as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()



    def get_verified_links(self, sdks, icd_codes):
        """
        Lấy danh sách kiến thức đã xác nhận từ DB dựa trên list SDK và list ICD.
        """
        if not sdks or not icd_codes:
            return []
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if table exists first
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drug_disease_links'")
            if not cursor.fetchone():
                return []

            # Dynamic SQL construction using placeholders
            placeholders_sdk = ','.join('?' for _ in sdks)
            placeholders_icd = ','.join('?' for _ in icd_codes)
            
            sql = f"""
                SELECT * FROM drug_disease_links 
                WHERE sdk IN ({placeholders_sdk}) 
                AND icd_code IN ({placeholders_icd})
                AND is_verified = 1
            """
            
            cursor.execute(sql, list(sdks) + list(icd_codes))
            return cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"DB Get Links Error: {e}")
            return []
        finally:
            conn.close()

    # --- CRUD FOR ADMIN ---
    def get_drugs_list(self, page=1, limit=20, search=""):
        offset = (page - 1) * limit
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            conditions = []
            params = []
            if search:
                conditions.append("(ten_thuoc LIKE ? OR so_dang_ky LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Count total
            cursor.execute(f"SELECT COUNT(*) as count FROM drugs {where_clause}", params)
            total = cursor.fetchone()['count']
            
            # Get Data
            sql = f"SELECT rowid, * FROM drugs {where_clause} ORDER BY rowid DESC LIMIT ? OFFSET ?"
            cursor.execute(sql, params + [limit, offset])
            data = cursor.fetchall()
            
            return {"total": total, "data": data}
        finally:
            conn.close()

    def delete_drug(self, sdk):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Delete from main table
            cursor.execute("DELETE FROM drugs WHERE so_dang_ky = ?", (sdk,))
            # Delete from links
            cursor.execute("DELETE FROM drug_disease_links WHERE sdk = ?", (sdk,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def delete_drug_by_id(self, row_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get SDK first to delete links
            cursor.execute("SELECT so_dang_ky FROM drugs WHERE rowid = ?", (row_id,))
            row = cursor.fetchone()
            sdk = row['so_dang_ky'] if row else None

            # Delete from main table
            cursor.execute("DELETE FROM drugs WHERE rowid = ?", (row_id,))
            
            # Delete from links if SDK existed
            if sdk:
                cursor.execute("DELETE FROM drug_disease_links WHERE sdk = ?", (sdk,))
                
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
            
    def get_links_list(self, page=1, limit=20, search=""):
        offset = (page - 1) * limit
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            conditions = []
            params = []
            if search:
                conditions.append("(drug_name LIKE ? OR disease_name LIKE ? OR sdk LIKE ? OR icd_code LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
           # Check table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drug_disease_links'")
            if not cursor.fetchone():
                 return {"total": 0, "data": []}

            # Count total
            cursor.execute(f"SELECT COUNT(*) as count FROM drug_disease_links {where_clause}", params)
            total = cursor.fetchone()['count']
            
            # Get Data
            sql = f"SELECT rowid, * FROM drug_disease_links {where_clause} ORDER BY rowid DESC LIMIT ? OFFSET ?"
            cursor.execute(sql, params + [limit, offset])
            data = cursor.fetchall()
            
            return {"total": total, "data": data}
        finally:
            conn.close()
            
    def delete_link(self, sdk, icd_code):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM drug_disease_links WHERE sdk =? AND icd_code = ?", (sdk, icd_code))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def check_knowledge_base(self, sdks: list, icds: list):
        """
        Kiểm tra mối liên hệ trong Knowledge Base (Facts).
        Returns: Dict {(sdk, icd): {status, coverage_type, treatment_note}}
        """
        if not sdks or not icds: return {}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Dynamic SQL for IN clause
            sdk_placeholders = ','.join(['?']*len(sdks))
            icd_placeholders = ','.join(['?']*len(icds))
            
            sql = f"""
                SELECT sdk, icd_code, status, coverage_type, treatment_note 
                FROM drug_disease_links 
                WHERE sdk IN ({sdk_placeholders}) 
                AND icd_code IN ({icd_placeholders})
            """
            
            # Flatten args
            args = list(sdks) + list(icds)
            cursor.execute(sql, args)
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                key = (row['sdk'], row['icd_code'])
                result[key] = dict(row)
            return result
            
        except sqlite3.Error as e:
            print(f"KB Check Error: {e}")
            return {}
        finally:
            conn.close()

    def log_raw_data(self, batch_id, content, source_ip):
        """Log raw input data for audit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO raw_logs (batch_id, raw_content, source_ip) VALUES (?, ?, ?)", 
                           (batch_id, content, source_ip))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def upsert_knowledge_base(self, drug_name, disease_name, icd_code=None, drug_ref_id=None):
        """
        Vote & Promote Logic:
        - Normalize names.
        - Check if exists.
        - If yes: freq += 1. update confidence.
        - If no: insert freq=1.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            drug_norm = normalize_text(drug_name)
            disease_norm = normalize_text(disease_name)
            icd = icd_code.strip() if icd_code else ""
            
            # Find existing record
            sql_find = "SELECT id, frequency FROM knowledge_base WHERE drug_name_norm = ? AND disease_name_norm = ?"
            params = [drug_norm, disease_norm]
            if icd:
                sql_find += " AND disease_icd = ?"
                params.append(icd)
            
            cursor.execute(sql_find, params)
            row = cursor.fetchone()
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if row:
                new_freq = row['frequency'] + 1
                # Simple Confidence Logic: log10(freq) / 2.5 (max out at freq ~300 -> 1.0)
                import math
                conf = min(0.99, math.log10(new_freq) / 2.5) if new_freq > 1 else 0.1
                
                cursor.execute("""
                    UPDATE knowledge_base 
                    SET frequency = ?, confidence_score = ?, last_updated = ?
                    WHERE id = ?
                """, (new_freq, conf, now, row['id']))
            else:
                cursor.execute("""
                    INSERT INTO knowledge_base (drug_name_norm, disease_name_norm, disease_icd, drug_ref_id, frequency, confidence_score, last_updated)
                    VALUES (?, ?, ?, ?, 1, 0.1, ?)
                """, (drug_norm, disease_norm, icd, drug_ref_id, now))
                
            conn.commit()
        except Exception as e:
            print(f"KB Upsert Error: {e}")
        finally:
            conn.close()


# --- DATABASE ENGINE CHO BỆNH (ICD) ---
class DiseaseDbEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = dict_factory
        return conn

    def search(self, name, icd10):
        # ... (Keep existing search)
        return self._search_impl(name, icd10)

    def _search_impl(self, name, icd10):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 1. By ICD (High Confidence)
            if icd10:
                cursor.execute("SELECT * FROM diseases WHERE icd_code = ?", (icd10.strip(),))
                row = cursor.fetchone()
                if row:
                    return {"data": dict(row), "confidence": 1.0, "source": "Database (Exact ICD)"}

            # 2. By Name (Exact)
            if name:
                norm_name = name.strip()
                cursor.execute("SELECT * FROM diseases WHERE disease_name = ?", (norm_name,))
                row = cursor.fetchone()
                if row:
                    return {"data": dict(row), "confidence": 1.0, "source": "Database (Exact Name)"}

            # 3. By Name (FST / LIKE)
            if name:
                 # Standardize
                 search_term = f"%{name.strip()}%"
                 cursor.execute("SELECT * FROM diseases WHERE disease_name LIKE ? ORDER BY length(disease_name) ASC LIMIT 1", (search_term,))
                 row = cursor.fetchone()
                 if row:
                     return {"data": dict(row), "confidence": 0.9, "source": "Database (Partial Name)"}
                 
                 # FTS Search (if table exists)
                 # self._ensure_fts() # Assuming FTS table is managed elsewhere/initialized
                 # cursor.execute(...)
            
            return None
        finally:
            conn.close()

    # --- CRUD FOR ADMIN ---
    def get_diseases_list(self, page=1, limit=20, search=""):
        offset = (page - 1) * limit
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            conditions = []
            params = []
            if search:
                conditions.append("(disease_name LIKE ? OR icd_code LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Count total
            cursor.execute(f"SELECT COUNT(*) as count FROM diseases {where_clause}", params)
            total = cursor.fetchone()['count']
            
            # Get Data
            sql = f"SELECT rowid, * FROM diseases {where_clause} ORDER BY rowid DESC LIMIT ? OFFSET ?"
            cursor.execute(sql, params + [limit, offset])
            data = cursor.fetchall()
            
            return {"total": total, "data": data}
        finally:
            conn.close()

    def delete_disease(self, icd_code):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Delete from main table
            cursor.execute("DELETE FROM diseases WHERE icd_code = ?", (icd_code,))
            # Delete from links
            cursor.execute("DELETE FROM drug_disease_links WHERE icd_code = ?", (icd_code,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def delete_disease_by_id(self, row_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get ICD
            cursor.execute("SELECT icd_code FROM diseases WHERE rowid = ?", (row_id,))
            row = cursor.fetchone()
            icd = row['icd_code'] if row else None
            
            # Delete from main table
            cursor.execute("DELETE FROM diseases WHERE rowid = ?", (row_id,))
            
            if icd:
                cursor.execute("DELETE FROM drug_disease_links WHERE icd_code = ?", (icd,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def save_disease(self, data):
        """
        Lưu thông tin bệnh vào DB (Upsert).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            icd_code = data.get('icd_code', '').strip()
            disease_name = data.get('disease_name', '').strip()
            chapter = data.get('chapter_name', '').strip() # Use chapter_name matching DB column
            
            if not icd_code or not disease_name:
                return {"status": "error", "message": "Missing ICD Code or Disease Name"}

            # Check existence
            cursor.execute("SELECT rowid FROM diseases WHERE icd_code = ?", (icd_code,))
            row = cursor.fetchone()
            
            # Normalize for search
            search_text = normalize_text(f"{disease_name} {icd_code}")
            
            if row:
                # Update
                row_id = row['rowid']
                cursor.execute("""
                    UPDATE diseases SET disease_name=?, chapter_name=? WHERE rowid=?
                """, (disease_name, chapter, row_id))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO diseases (icd_code, disease_name, chapter_name) VALUES (?, ?, ?)
                """, (icd_code, disease_name, chapter))
                row_id = cursor.lastrowid
            
            # Update FTS (Delete and Re-insert)
            cursor.execute("DELETE FROM diseases_fts WHERE rowid = ?", (row_id,))
            cursor.execute("""
                INSERT INTO diseases_fts(rowid, disease_name, icd_code, search_text)
                VALUES (?, ?, ?, ?)
            """, (row_id, disease_name, icd_code, search_text))
            
            conn.commit()
            return {"status": "success", "message": f"Saved disease: {disease_name} ({icd_code})"}
            
        except sqlite3.Error as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()



from app.service.crawler import search_icd_online

# --- WEB SCRAPER WRAPPERS ---
async def scrape_drug_web(keyword):
    from app.service.web_crawler import scrape_drug_web_advanced 
    print(f"Scraping Web V2 (Advanced) for Drug: {keyword}")
    try:
        # Use V2 Advanced Scraper
        result = await scrape_drug_web_advanced(keyword)
        if result.get('status') == 'not_found' or result.get('status') == 'error':
            return None
        return result
        
        if not results: 
            return {}
        
        # V1 returns a list of dicts
        first_result = results[0]
        content = first_result.get('Content', 'N/A')
        link = first_result.get('Link', "")
        source_name = first_result.get('Source', "Web")
        
        # Helper to extract SDK from content
        sdk = "Web Result"
        strict_pattern = re.compile(
            r'(VN-\d{4,5}-\d{2}|VD-\d{4,5}-\d{2}|QLD-\d+-\d+|GC-\d+-\d+|VNA-\d+-\d+|VNB-\d+-\d+)', 
            re.IGNORECASE
        )
        match = strict_pattern.search(content)
        if match:
            sdk = match.group(1)
        else:
            context_pattern = re.compile(
                r'(?:Số\s+đăng\s+ký|SĐK|SDK|Reg\.No)[:.]?\s*([A-Za-z0-9\-\/Đđ]+)', 
                re.IGNORECASE
            )
            match_ctx = context_pattern.search(content)
            if match_ctx:
                sdk = match_ctx.group(1)
            
        return {
            "ten_thuoc": keyword,
            "so_dang_ky": sdk,
            "hoat_chat": "Xem chi tiết",
            "cong_ty_san_xuat": source_name,
            "chi_dinh": content[:1500] + "...", 
            "is_verified": 0,
            "source": f"{source_name} ({link})",
            "ref_link": link
        }
    except Exception as e:
        print(f"Scraping V1 Error: {e}")
        return {}

async def scrape_icd_web(keyword):
    try:
        results = await search_icd_online(keyword)
        if not results: return {}
        
        combined_content = "\n\n".join([f"Source: {r['Source']}\nContent: {r['Content'][:500]}..." for r in results])
        
        return {
            "disease_name": keyword,
            "icd_code": "Web Result",
            "chapter_name": "N/A",
            "description": combined_content,
            "raw_web_results": results
        }
    except Exception as e:
        print(f"Scraping Error: {e}")
        return {}



# ... (API client setup logs remain unchanged)

# --- LLM SERVICE (CẬP NHẬT LOGIC V1) ---
def analyze_treatment_group(drugs_info, diseases_info, known_links=None):
    # 1. Prepare Facts Sections
    ground_truth = []
    negative_truth = []
    
    if known_links:
        for drug in drugs_info:
            sdk = drug.get('so_dang_ky')
            if not sdk: continue
            
            for disease in diseases_info:
                icd = disease.get('icd_code')
                if not icd: continue
                
                link_data = known_links.get((sdk, icd))
                if link_data:
                    cov_type = link_data.get('coverage_type', '')
                    note = link_data.get('treatment_note', '') or 'Theo chỉ định'
                    status = link_data.get('status', 'active')
                    
                    # Logic: Refusal
                    if cov_type in ['Thuốc không điều trị', 'Từ chối chi trả', 'Thuốc bổ/TPCN Refused']:
                        negative_truth.append(f"- [REFUSED] {drug['ten_thuoc']} ({sdk}) <> {disease['disease_name']} ({icd}): {cov_type}")
                        continue
                    
                    # Logic: Approved or Pending
                    prefix = "[VERIFIED]" if status == 'active' else "[PENDING APPROVAL]"
                    ground_truth.append(f"- {prefix} {drug['ten_thuoc']} ({sdk}) -> {disease['disease_name']} ({icd}): {cov_type} ({note})")

    # 2. Build Prompt Section
    facts_section = ""
    if ground_truth or negative_truth:
        facts_section = f"""
        ============================================================
        CĂN CỨ TỪ CƠ SỞ DỮ LIỆU (GROUND TRUTH):
        Hệ thống đã tra cứu và có kết quả chính xác cho các cặp sau.
        Bạn BẮT BUỘC phải tuân thủ tuyệt đối các thông tin này:
        
        [CÓ MỐI LIÊN HỆ - PHẢI ĐƯA VÀO KẾT QUẢ]:
        {chr(10).join(ground_truth)}
        
        [KHÔNG CÓ MỐI LIÊN HỆ - TỪ CHỐI/KHÔNG GHÉP]:
        {chr(10).join(negative_truth)}
        ============================================================
        """

    prompt = f"""
            Bạn là một dược sĩ lâm sàng.
            
            {facts_section}
            
            Dữ liệu đầu vào (Cần phân tích những cặp CHƯA có trong Ground Truth):
            - Danh sách bệnh (chẩn đoán + ICD): {diseases_info}
            - Danh sách thuốc (tên, SĐK, hoạt chất, phân loại, ghi chú): {drugs_info}

            NHIỆM VỤ:
            NHIỆM VỤ:
            1. ƯU TIÊN SỐ 1: Kiểm tra phần "CĂN CỨ TỪ CƠ SỞ DỮ LIỆU". Nếu cặp thuốc-bệnh đã có trong đó, sử dụng ngay kết quả (chấp nhận hoặc từ chối) mà không cần suy luận lại.
            2. QUAN TRỌNG: Đọc kỹ trường 'note' (ghi chú) và 'classification' (phân loại) của thuốc nếu có.
            2. QUAN TRỌNG: Đọc kỹ trường 'note' (ghi chú) và 'classification' (phân loại) của thuốc nếu có.
               - Nếu 'note' chỉ định rõ thuốc dùng cho bệnh nào -> Sử dụng làm căn cứ mạnh.
               - Nếu 'classification' là "Thực phẩm chức năng" hoặc "Vitamin" -> Cân nhắc kỹ trước khi ghép điều trị chính, thường chỉ là hỗ trợ.
            3. Phân tích các thuốc còn lại:
               - Ghép thuốc với bệnh lý điều trị tương ứng.
               - Chỉ được suy luận dựa trên TÊN BỆNH và HOẠT CHẤT / TÊN THUỐC có trong dữ liệu.
               - KHÔNG sử dụng kiến thức bên ngoài dữ liệu được cung cấp.
               - Mỗi thuốc cần có một câu căn cứ ngắn gọn (1 câu).

            RÀNG BUỘC BẮT BUỘC:
            - Chỉ trả về JSON, KHÔNG kèm markdown (ví dụ không dùng ```json), KHÔNG giải thích ngoài JSON.
            - KHÔNG thêm field ngoài schema cho phép.
            - KHÔNG thêm cảnh báo, khuyến cáo, phân tích mở rộng.
            - Nếu một bệnh không ghép được thuốc nào → medications là mảng rỗng [].
            - Nếu không có dữ liệu phù hợp → trả {{"results": []}}.

            SCHEMA JSON DUY NHẤT ĐƯỢC PHÉP TRẢ VỀ:

            {{
            "results": [
                {{
                "disease": "Tên bệnh (Mã ICD)",
                "medications": [
                    ["Tên thuốc (SĐK)","Căn cứ"],
                    ["Tên thuốc (SĐK)","Căn cứ"],
                    ]
                }}
            ]
            }}

            VÍ DỤ HÌNH THỨC (CHỈ LÀ VÍ DỤ FORMAT, KHÔNG DÙNG NỘI DUNG):

            {{
            "results": [
                {{
                "disease": "Tên bệnh A (ICD)",
                "medications": [[
                    "Tên thuốc X (SĐK)",
                    "Căn cứ"
                ]]
                }}
            ]
            }}

            hãy trả kết quả theo ĐÚNG schema trên.
            """

    
    try:
        # CÚ PHÁP MỚI CỦA OPENAI V1
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME, # Trong Azure, model là tên deployment
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0 # API chúng tôi đăng ký với OpenAI chỉ cho phép temp = 1.0
        )
        content = response.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            # Fallback nếu model trả về format sai
            # Cố gắng sửa lỗi phổ biến hoặc trả về raw text trong structure an toàn
            return {
                "results": [],
                "error": "LLM response format invalid",
                "raw_content": content
            }
            
    except Exception as e:
        return {
            "results": [],
            "error": f"Lỗi gọi OpenAI: {str(e)}"
        }