"""
Drug Matcher Module - Multistage Drug Matching Engine
======================================================
Standalone implementation với 4 tầng matching:
1. Exact Match (100%)
2. Partial/LIKE Match (95%)
3. RapidFuzz Token Sort (88%)
4. TF-IDF Vector Search (90%)
"""

import sqlite3
import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import numpy as np

from .normalizer import normalize_for_matching

# Setup logging
logger = logging.getLogger("mapping_drugs.matcher")
logger.setLevel(logging.DEBUG)

# File handler for detailed matching logs
# Use /app/logs/mapping which syncs to host via Docker volume mount
_log_dir = "/app/logs/mapping"
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, f"matching_{datetime.now().strftime('%Y%m%d')}.log")

if not logger.handlers:
    fh = logging.FileHandler(_log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Also add console handler for immediate feedback
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Lazy imports để tránh lỗi khi chưa cài thư viện
_rapidfuzz_available = False
_sklearn_available = False
_bm25_available = False

try:
    from rapidfuzz import process, fuzz
    _rapidfuzz_available = True
except ImportError:
    pass

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _sklearn_available = True
except ImportError:
    pass

try:
    from rank_bm25 import BM25Okapi
    _bm25_available = True
except ImportError:
    pass


class DrugMatcher:
    """
    Multistage Drug Matcher - Tìm kiếm thuốc trong Database.
    
    Không gọi API, chỉ query trực tiếp vào SQLite.
    
    Usage:
        matcher = DrugMatcher(db_path="path/to/medical.db")
        result = matcher.match("Paracetamol 500mg")
        # result = {"status": "FOUND", "data": {...}, "confidence": 1.0, "method": "EXACT_MATCH"}
    """
    
    # Thresholds
    FUZZY_THRESHOLD = 85.0       # RapidFuzz score >= 85
    VECTOR_THRESHOLD = 0.75      # Cosine similarity > 0.75
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Khởi tạo DrugMatcher.
        
        Args:
            db_path: Đường dẫn tới medical.db. Nếu None, sẽ tự detect từ env.
        """
        if db_path is None:
            db_path = os.getenv(
                "DB_PATH", 
                os.path.join(os.path.dirname(__file__), "..", "database", "medical.db")
            )
        
        self.db_path = db_path
        
        # Cache for fuzzy/vector/bm25 search
        self.vectorizer = None
        self.tfidf_matrix = None
        self.bm25_index = None  # BM25 index
        self.bm25_corpus = []   # Tokenized corpus for BM25
        self.drug_cache: List[Dict] = []
        self.fuzzy_names: List[str] = []
        
        # Load cache on init
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load drugs vào RAM cho fuzzy/vector/bm25 search."""
        if not os.path.exists(self.db_path):
            print(f"[DrugMatcher] WARNING: Database not found at {self.db_path}")
            return
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Chỉ lấy thuốc đã verified có SDK
            cursor.execute("""
                SELECT id, ten_thuoc, so_dang_ky, hoat_chat, search_text 
                FROM drugs 
                WHERE is_verified=1 AND so_dang_ky IS NOT NULL AND so_dang_ky != ''
            """)
            rows = cursor.fetchall()
            self.drug_cache = [dict(row) for row in rows]
            
            if self.drug_cache:
                # Build fuzzy names list
                self.fuzzy_names = [d['ten_thuoc'] for d in self.drug_cache]
                
                # Build corpus for vectorizers
                corpus = [d['search_text'] or d['ten_thuoc'] for d in self.drug_cache]
                
                # Build TF-IDF matrix nếu sklearn available
                if _sklearn_available:
                    self.vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
                    self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
                
                # Build BM25 index nếu rank_bm25 available
                if _bm25_available:
                    # Tokenize corpus for BM25
                    self.bm25_corpus = [doc.lower().split() for doc in corpus]
                    self.bm25_index = BM25Okapi(self.bm25_corpus)
                    logger.info(f"[DrugMatcher] BM25 index built with {len(self.bm25_corpus)} documents")
                
                print(f"[DrugMatcher] Loaded {len(self.drug_cache)} drugs into cache")
        except Exception as e:
            print(f"[DrugMatcher] Cache load error: {e}")
        finally:
            conn.close()
    
    def match(self, drug_name: str) -> Dict[str, Any]:
        """
        Tìm thuốc trong DB theo thứ tự ưu tiên:
        1. Exact Match (100%)
        2. Partial/LIKE Match (95%)
        3. RapidFuzz (88%)
        4. TF-IDF Vector (90%)
        
        Args:
            drug_name: Tên thuốc cần tìm
            
        Returns:
            {
                "status": "FOUND" | "NOT_FOUND",
                "data": {...} | None,
                "confidence": float (0.0 - 1.0),
                "method": str
            }
        """
        if not drug_name or not drug_name.strip():
            logger.warning(f"[MATCH] Empty input received")
            return self._not_found("EMPTY_INPUT")
        
        raw_query = drug_name.strip()
        normalized = normalize_for_matching(drug_name)
        
        logger.info(f"[MATCH] ========== START MATCHING ==========")
        logger.info(f"[MATCH] Input: '{raw_query}'")
        logger.info(f"[MATCH] Normalized: '{normalized}'")
        
        if not os.path.exists(self.db_path):
            logger.error(f"[MATCH] Database not found: {self.db_path}")
            return self._not_found("DB_NOT_FOUND")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # === LEVEL 1: EXACT MATCH ===
            logger.debug(f"[MATCH] Step 1: Trying EXACT MATCH with '{raw_query}'")
            result = self._exact_match(cursor, raw_query)
            if result:
                matched_name = result['data'].get('ten_thuoc', 'N/A')
                logger.info(f"[MATCH] ✅ FOUND at Step 1 (EXACT): '{matched_name}'")
                return result
            logger.debug(f"[MATCH] Step 1: No exact match for '{raw_query}'")
            
            # Try với normalized
            if normalized != raw_query.lower():
                logger.debug(f"[MATCH] Step 1b: Trying EXACT MATCH with normalized '{normalized}'")
                result = self._exact_match(cursor, normalized)
                if result:
                    result["method"] = "EXACT_MATCH (normalized)"
                    matched_name = result['data'].get('ten_thuoc', 'N/A')
                    logger.info(f"[MATCH] ✅ FOUND at Step 1b (EXACT normalized): '{matched_name}'")
                    return result
                logger.debug(f"[MATCH] Step 1b: No exact match for normalized")
            
            # === LEVEL 2: PARTIAL/LIKE MATCH ===
            logger.debug(f"[MATCH] Step 2: Trying PARTIAL MATCH with '{normalized}'")
            result = self._partial_match(cursor, normalized)
            if result:
                matched_name = result['data'].get('ten_thuoc', 'N/A')
                logger.info(f"[MATCH] ✅ FOUND at Step 2 (PARTIAL): '{matched_name}'")
                return result
            logger.debug(f"[MATCH] Step 2: No partial match")
            
            # === LEVEL 3: RAPIDFUZZ ===
            if _rapidfuzz_available and self.drug_cache:
                logger.debug(f"[MATCH] Step 3: Trying FUZZY MATCH with '{raw_query}'")
                result = self._fuzzy_match(cursor, raw_query)
                if result:
                    matched_name = result['data'].get('ten_thuoc', 'N/A')
                    logger.info(f"[MATCH] ✅ FOUND at Step 3 (FUZZY): '{matched_name}' - {result['method']}")
                    return result
                logger.debug(f"[MATCH] Step 3: No fuzzy match above threshold {self.FUZZY_THRESHOLD}")
            else:
                logger.debug(f"[MATCH] Step 3: Skipped (rapidfuzz not available or cache empty)")
            
            # === LEVEL 4: TF-IDF VECTOR ===
            if _sklearn_available and self.vectorizer and self.tfidf_matrix is not None:
                logger.debug(f"[MATCH] Step 4: Trying VECTOR MATCH with '{normalized}'")
                result = self._vector_match(cursor, normalized)
                if result:
                    matched_name = result['data'].get('ten_thuoc', 'N/A')
                    logger.info(f"[MATCH] ✅ FOUND at Step 4 (VECTOR): '{matched_name}' - {result['method']}")
                    return result
                logger.debug(f"[MATCH] Step 4: No vector match above threshold {self.VECTOR_THRESHOLD}")
            else:
                logger.debug(f"[MATCH] Step 4: Skipped (sklearn not available or vectorizer not ready)")
            
            # === LEVEL 5: BM25 ===
            if _bm25_available and self.bm25_index:
                logger.debug(f"[MATCH] Step 5: Trying BM25 MATCH with '{normalized}'")
                result = self._bm25_match(cursor, normalized)
                if result:
                    matched_name = result['data'].get('ten_thuoc', 'N/A')
                    logger.info(f"[MATCH] ✅ FOUND at Step 5 (BM25): '{matched_name}' - {result['method']}")
                    return result
                logger.debug(f"[MATCH] Step 5: No BM25 match above threshold")
            else:
                logger.debug(f"[MATCH] Step 5: Skipped (rank_bm25 not available or index not built)")
            
            # === NOT FOUND ===
            logger.warning(f"[MATCH] ❌ NOT FOUND: '{raw_query}' - All 5 steps failed")
            return self._not_found("NO_MATCH")
        
        finally:
            conn.close()
    
    def _exact_match(self, cursor, query: str) -> Optional[Dict]:
        """Level 1: Exact name match."""
        cursor.execute("""
            SELECT * FROM drugs 
            WHERE ten_thuoc = ? AND is_verified=1 AND so_dang_ky IS NOT NULL
        """, (query,))
        row = cursor.fetchone()
        
        if row:
            return {
                "status": "FOUND",
                "data": dict(row),
                "confidence": 1.0,
                "method": "EXACT_MATCH"
            }
        return None
    
    def _partial_match(self, cursor, normalized: str) -> Optional[Dict]:
        """Level 2: Partial/LIKE match."""
        cursor.execute("""
            SELECT * FROM drugs 
            WHERE ten_thuoc LIKE ? AND is_verified=1 AND so_dang_ky IS NOT NULL
            LIMIT 1
        """, (f"%{normalized}%",))
        row = cursor.fetchone()
        
        if row:
            return {
                "status": "FOUND",
                "data": dict(row),
                "confidence": 0.95,
                "method": "PARTIAL_MATCH"
            }
        return None
    
    def _fuzzy_match(self, cursor, raw_query: str) -> Optional[Dict]:
        """Level 3: RapidFuzz token sort ratio."""
        fuzzy_res = process.extractOne(
            raw_query, 
            self.fuzzy_names, 
            scorer=fuzz.token_sort_ratio
        )
        
        if fuzzy_res:
            match_name, score, idx = fuzzy_res
            if score >= self.FUZZY_THRESHOLD:
                match_data = self.drug_cache[idx]
                cursor.execute("SELECT * FROM drugs WHERE id = ?", (match_data['id'],))
                full_row = cursor.fetchone()
                if full_row:
                    return {
                        "status": "FOUND",
                        "data": dict(full_row),
                        "confidence": 0.88,
                        "method": f"FUZZY_MATCH (score={score:.1f})"
                    }
        return None
    
    def _vector_match(self, cursor, normalized: str) -> Optional[Dict]:
        """Level 4: TF-IDF cosine similarity."""
        query_vec = self.vectorizer.transform([normalized])
        cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        if cosine_sim.size > 0:
            best_idx = int(np.argmax(cosine_sim))
            best_score = float(cosine_sim[best_idx])
            
            if best_score > self.VECTOR_THRESHOLD:
                match_data = self.drug_cache[best_idx]
                cursor.execute("SELECT * FROM drugs WHERE id = ?", (match_data['id'],))
                full_row = cursor.fetchone()
                if full_row:
                    return {
                        "status": "FOUND",
                        "data": dict(full_row),
                        "confidence": 0.90,
                        "method": f"VECTOR_MATCH (cosine={best_score:.2f})"
                    }
        return None
    
    def _bm25_match(self, cursor, normalized: str) -> Optional[Dict]:
        """Level 5: BM25 Okapi ranking."""
        # Tokenize query
        query_tokens = normalized.lower().split()
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        if len(scores) > 0:
            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])
            
            # BM25 scores vary widely, use relative threshold
            # Score > 5 is typically a good match
            if best_score > 5.0:
                match_data = self.drug_cache[best_idx]
                cursor.execute("SELECT * FROM drugs WHERE id = ?", (match_data['id'],))
                full_row = cursor.fetchone()
                if full_row:
                    return {
                        "status": "FOUND",
                        "data": dict(full_row),
                        "confidence": 0.85,
                        "method": f"BM25_MATCH (score={best_score:.2f})"
                    }
        return None
    
    def _not_found(self, reason: str) -> Dict[str, Any]:
        """Return NOT_FOUND result."""
        return {
            "status": "NOT_FOUND",
            "data": None,
            "confidence": 0.0,
            "method": reason
        }
    
    def match_batch(self, drug_names: List[str]) -> List[Dict[str, Any]]:
        """
        Match nhiều thuốc cùng lúc.
        
        Args:
            drug_names: Danh sách tên thuốc
            
        Returns:
            Danh sách kết quả match
        """
        return [self.match(name) for name in drug_names]
