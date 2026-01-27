"""
KB Fuzzy Match Service - Fuzzy matching for knowledge_base drug names.
Uses TF-IDF + RapidFuzz similar to DrugSearchService, but on knowledge_base data.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.database.core import DatabaseCore
from app.core.utils import normalize_for_matching

class KBFuzzyMatchService:
    """
    Fuzzy matching service specifically for knowledge_base table.
    Finds best drug_name_norm match given an input drug name.
    """
    
    def __init__(self, db_core: DatabaseCore = None):
        if db_core is None:
            self.db_core = DatabaseCore()
        else:
            self.db_core = db_core
            
        # Vector cache
        self.vectorizer = None
        self.tfidf_matrix = None
        self.drug_names = []  # distinct drug_name_norm values
        self.cache_loaded = False
    
    def refresh_cache(self):
        """Force reload cache from database. Call after data ingest."""
        print("[KBFuzzyMatch] Refreshing cache...")
        self.cache_loaded = False
        self.drug_names = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._load_cache()
    
    def _load_cache(self):
        """Load all distinct drug_name_norm from knowledge_base for vector matching"""
        if self.cache_loaded:
            return
        
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all distinct drug names from knowledge_base
            cursor.execute("""
                SELECT DISTINCT drug_name_norm 
                FROM knowledge_base 
                WHERE drug_name_norm IS NOT NULL 
                  AND drug_name_norm != ''
                  AND drug_name_norm != '_icd_list_'
            """)
            rows = cursor.fetchall()
            print(f"[KBFuzzyMatch] Query returned {len(rows)} rows")
            
            # Handle row access (Dict vs Tuple)
            # If Dict (PG RealDictCursor or SQLite dict_factory via core) -> row['drug_name_norm']
            # If Tuple (raw) -> row[0]
            # Since Core standardizes on dict-like usually, but let's be safe.
            
            # Actually core returns dicts by default for sqlite (dict_factory) and PG (RealDictCursor).
            # So row['drug_name_norm'] is safe.
            # But wait, if someone didn't use dict_factory...
            # DatabaseCore: 
            # SQLite -> dict_factory
            # Postgres -> RealDictCursor
            # So always dict access.
            
            self.drug_names = []
            for row in rows:
                val = row['drug_name_norm'] if isinstance(row, dict) else row[0]
                if val and val.strip():
                    self.drug_names.append(val)

            print(f"[KBFuzzyMatch] Filtered to {len(self.drug_names)} drug names")
            
            if self.drug_names:
                # Build TF-IDF matrix
                self.vectorizer = TfidfVectorizer(
                    token_pattern=r"(?u)\b\w+\b",
                    ngram_range=(1, 2)  # Include bigrams for better matching
                )
                self.tfidf_matrix = self.vectorizer.fit_transform(self.drug_names)
                self.cache_loaded = True
                print(f"[KBFuzzyMatch] Loaded {len(self.drug_names)} unique drug names from KB, matrix shape: {self.tfidf_matrix.shape}")
            else:
                print("[KBFuzzyMatch] WARNING: No drug names found in knowledge_base!")
                
        except Exception as e:
            import traceback
            print(f"[KBFuzzyMatch] Cache Load Error: {e}")
            traceback.print_exc()
        finally:
            conn.close()
    
    def find_best_match(self, input_name: str, min_score: float = 0.5) -> dict | None:
        """
        Find best matching drug_name_norm from knowledge_base.
        
        Strategy:
        1. Exact match (score = 1.0)
        2. LIKE partial match (score = 0.95)
        3. RapidFuzz match (score = fuzzy_score * 0.01)
        4. TF-IDF vector match (score = cosine_sim)
        
        Returns: {"drug_name_norm": str, "score": float, "method": str} or None
        """
        if not input_name:
            return None
        
        normalized_input = normalize_for_matching(input_name)
        
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. EXACT MATCH
            cursor.execute("""
                SELECT DISTINCT drug_name_norm FROM knowledge_base 
                WHERE drug_name_norm = ?
                LIMIT 1
            """, (normalized_input,))
            row = cursor.fetchone()
            if row:
                name = row['drug_name_norm'] if isinstance(row, dict) else row[0]
                return {"drug_name_norm": name, "score": 1.0, "method": "exact"}
            
            # 2. LIKE PARTIAL MATCH (contains)
            cursor.execute("""
                SELECT DISTINCT drug_name_norm FROM knowledge_base 
                WHERE drug_name_norm LIKE ?
                LIMIT 1
            """, (f"%{normalized_input}%",))
            row = cursor.fetchone()
            if row:
                name = row['drug_name_norm'] if isinstance(row, dict) else row[0]
                return {"drug_name_norm": name, "score": 0.95, "method": "partial"}
            
            # 3. RAPIDFUZZ MATCH
            self._load_cache()
            
            try:
                from rapidfuzz import process, fuzz
                if self.drug_names:
                    result = process.extractOne(
                        normalized_input, 
                        self.drug_names, 
                        scorer=fuzz.token_sort_ratio,
                        score_cutoff=70  # Minimum 70% similarity
                    )
                    if result:
                        match_name, score, idx = result
                        fuzzy_score = score / 100.0  # Normalize to 0-1
                        if fuzzy_score >= min_score:
                            return {"drug_name_norm": match_name, "score": fuzzy_score, "method": f"fuzzy({score:.0f}%)"}
            except ImportError:
                print("[KBFuzzyMatch] rapidfuzz not installed, skipping fuzzy match")
            except Exception as e:
                print(f"[KBFuzzyMatch] RapidFuzz error: {e}")
            
            # 4. TF-IDF VECTOR MATCH
            if self.vectorizer and self.tfidf_matrix is not None:
                try:
                    query_vec = self.vectorizer.transform([normalized_input])
                    cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                    
                    if cosine_sim.size > 0:
                        best_idx = np.argmax(cosine_sim)
                        best_score = cosine_sim[best_idx]
                        
                        if best_score >= min_score:
                            return {
                                "drug_name_norm": self.drug_names[best_idx],
                                "score": float(best_score),
                                "method": f"tfidf({best_score:.2f})"
                            }
                except Exception as e:
                    print(f"[KBFuzzyMatch] TF-IDF error: {e}")
            
            return None
            
        finally:
            conn.close()
    
    def find_best_match_with_icd(self, input_name: str, disease_icd: str) -> dict | None:
        """
        Find best match AND verify it has data for the specific ICD code.
        Returns KB row data if found.
        """
        match = self.find_best_match(input_name)
        
        if not match:
            return None
        
        # Query knowledge_base with the matched drug name + ICD
        conn = self.db_core.get_connection()
        # conn.row_factory = sqlite3.Row # DatabaseCore handles this
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    drug_name_norm,
                    disease_icd,
                    treatment_type,
                    tdv_feedback,
                    frequency
                FROM knowledge_base
                WHERE drug_name_norm = ? AND disease_icd = ?
                ORDER BY 
                    (CASE WHEN tdv_feedback IS NOT NULL AND tdv_feedback != '' AND tdv_feedback != 'None' AND tdv_feedback != 'null' THEN 1 ELSE 0 END) DESC,
                    frequency DESC,
                    last_updated DESC
                LIMIT 1
            """, (match['drug_name_norm'], disease_icd))
            
            row = cursor.fetchone()
            if row:
                return {
                    "drug_name_norm": row['drug_name_norm'],
                    "disease_icd": row['disease_icd'],
                    "treatment_type": row['treatment_type'],
                    "tdv_feedback": row['tdv_feedback'],
                    "frequency": row['frequency'],
                    "match_score": match['score'],
                    "match_method": match['method']
                }
            
            return None
            
        finally:
            conn.close()
