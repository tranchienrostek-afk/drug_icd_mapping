import sqlite3
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.database.core import DatabaseCore
from app.core.utils import normalize_text, normalize_for_matching

class DrugSearchService:
    def __init__(self, db_core: DatabaseCore = None):
        if db_core is None:
            self.db_core = DatabaseCore()
        else:
            self.db_core = db_core
            
        self.vectorizer = None
        self.tfidf_matrix = None
        self.drug_cache = [] 
        self.fuzzy_names = []

    def _load_vector_cache(self):
        """Load data for vector search if not loaded or stale"""
        if self.vectorizer and self.tfidf_matrix is not None:
             return

        conn = self.db_core.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # Load verified drugs with SDK
            cursor.execute("SELECT id, ten_thuoc, so_dang_ky, search_text FROM drugs WHERE is_verified=1 AND so_dang_ky IS NOT NULL AND so_dang_ky != ''")
            rows = cursor.fetchall()
            self.drug_cache = [dict(row) for row in rows]
            
            if self.drug_cache:
                corpus = [d['search_text'] or d['ten_thuoc'] for d in self.drug_cache]
                self.vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
                self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
                self.fuzzy_names = [d['ten_thuoc'] for d in self.drug_cache]
        except Exception as e:
            print(f"Vector Cache Load Error: {e}")
        finally:
            conn.close()

    def search_drug_smart_sync(self, query_name: str):
        """
        Multistage Search (Synchronous Implementation):
        1. Exact Match (100%)
        2. Partial/Fuzzy SQL Match (95%)
        3. Vector/Semantic Match (90%)
        Returns: { data: dict, confidence: float, source: str } or None
        """
        conn = self.db_core.get_connection()
        # conn.row_factory = sqlite3.Row # Moved to core abstraction
        cursor = conn.cursor()
        
        # 1. Prepare variants
        raw_query = query_name.strip()
        db_normalized_query = normalize_for_matching(query_name)
        
        search_variants = []
        if raw_query: search_variants.append(raw_query)
        if db_normalized_query and db_normalized_query != raw_query.lower():
            search_variants.append(db_normalized_query)
        
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
                match_op = "ILIKE" if self.db_core.db_type == 'postgres' else "LIKE"
                cursor.execute(f"SELECT * FROM drugs WHERE ten_thuoc {match_op} ? AND is_verified=1 AND so_dang_ky IS NOT NULL", (f"%{variant}%",))
                row = cursor.fetchone()
                if row:
                     return {"data": dict(row), "confidence": 0.95, "source": f"Database (Partial{' Fallback' if variant != raw_query else ''})"}

            # 2.5. FUZZY MATCH (RapidFuzz) - Optimized to load cache only when needed
            self._load_vector_cache()
            try:
                from rapidfuzz import process, fuzz
                if self.drug_cache:
                     fuzzy_res = process.extractOne(raw_query, self.fuzzy_names, scorer=fuzz.token_sort_ratio)
                     if fuzzy_res:
                         match, score, idx = fuzzy_res
                         if score >= 85.0:
                             match_data = self.drug_cache[idx]
                             cursor.execute("SELECT * FROM drugs WHERE id = ?", (match_data['id'],))
                             full_row = cursor.fetchone()
                             if full_row:
                                 return {"data": dict(full_row), "confidence": 0.88, "source": f"Database (Fuzzy {score:.1f})"}
            except Exception as e:
                pass

            # 3. VECTOR SEARCH
            if self.vectorizer and self.tfidf_matrix is not None:
                query_vec = self.vectorizer.transform([db_normalized_query])
                cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                
                if cosine_sim.size > 0:
                    best_idx = np.argmax(cosine_sim)
                    best_score = cosine_sim[best_idx]
                    
                    if best_score > 0.75:
                        match_data = self.drug_cache[best_idx]
                        cursor.execute("SELECT * FROM drugs WHERE id = ?", (match_data['id'],))
                        full_row = cursor.fetchone()
                        if full_row:
                             return {"data": dict(full_row), "confidence": 0.90, "source": f"Database (Vector {best_score:.2f})"}

            return None
        finally:
            conn.close()

    async def search_drug_smart(self, query_name: str):
        """Async wrapper for smart search"""
        return self.search_drug_smart_sync(query_name)

    def search(self, query):
        """Legacy Search: FTS (SQLite) or Text Search (Postgres)"""
        if not query: return None
        
        query_clean = normalize_text(query)
        if not query_clean: return None

        try:
            conn = self.db_core.get_connection()
            cursor = conn.cursor()
            
            if self.db_core.db_type == 'postgres':
                # Postgres Text Search
                # Construct query: 'A & B & C'
                ts_query_str = " & ".join([w for w in query_clean.split() if w.strip()])
                if not ts_query_str: return None
                
                # Use to_tsquery with 'simple' config (matching index config)
                sql = "SELECT id, * FROM drugs WHERE search_vector @@ to_tsquery('simple', ?) LIMIT 1"
                cursor.execute(sql, (ts_query_str,))
            else:
                # SQLite FTS5
                # formatting: 'w* AND w*'
                search_term = " AND ".join([f"{w}*" for w in query_clean.split() if re.match(r'[a-zA-Z0-9]', w)])
                if not search_term: return None

                sql = "SELECT rowid FROM drugs_fts WHERE drugs_fts MATCH ? ORDER BY rank LIMIT 1"
                cursor.execute(sql, (search_term,))
            
            row = cursor.fetchone()
            
            if row:
                if self.db_core.db_type == 'postgres':
                    return dict(row) # Already full row
                else:
                    drug_id = row['rowid'] if isinstance(row, dict) else row[0]
                    cursor.execute("SELECT * FROM drugs WHERE id = ?", (drug_id,)) # Use 'id' alias for rowid
                    full_data = cursor.fetchone()
                    return dict(full_data) if full_data else None

            return None
        except Exception as e:
            print(f"Search Error: {e}")
            return None
        finally:
            conn.close()
