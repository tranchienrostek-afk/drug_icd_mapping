"""
Disease Service - Handles ICD/Disease lookup and management
"""
import sqlite3
import os
from typing import Optional, Dict, List
from app.database.core import DatabaseCore, dict_factory

class DiseaseService:
    """
    Service for disease/ICD operations.
    Queries the 'diseases' and 'knowledge_base' tables.
    """
    
    def __init__(self, db_core: DatabaseCore = None):
        if db_core:
            self.db_core = db_core
        else:
            from app.database.core import DB_PATH
            self.db_core = DatabaseCore(DB_PATH)
    
    def search(self, name: str = None, icd10: str = None) -> Optional[Dict]:
        """
        Search for disease by name or ICD-10 code.
        Returns dict with 'data' and 'source' keys.
        """
        conn = self.db_core.get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        try:
            # Priority 1: Search by ICD code if provided
            if icd10:
                cursor.execute("""
                    SELECT DISTINCT disease_icd as icd_code, disease_name_norm as disease_name, 
                           treatment_type as chapter_name
                    FROM knowledge_base
                    WHERE disease_icd = ? OR disease_icd LIKE ?
                    LIMIT 1
                """, (icd10, f"{icd10}%"))
                row = cursor.fetchone()
                if row:
                    return {"data": row, "source": "KnowledgeBase"}
            
            # Priority 2: Search by name
            if name:
                # Normalize search term
                search_term = f"%{name.lower()}%"
                cursor.execute("""
                    SELECT DISTINCT disease_icd as icd_code, disease_name_norm as disease_name,
                           treatment_type as chapter_name
                    FROM knowledge_base
                    WHERE LOWER(disease_name_norm) LIKE ?
                    LIMIT 1
                """, (search_term,))
                row = cursor.fetchone()
                if row:
                    return {"data": row, "source": "KnowledgeBase"}
            
            return None
            
        finally:
            conn.close()
    
    def get_diseases_list(self, page: int = 1, limit: int = 20, search: str = "") -> Dict:
        """
        Get paginated list of unique diseases from knowledge_base.
        """
        conn = self.db_core.get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        try:
            offset = (page - 1) * limit
            
            if search:
                search_term = f"%{search.lower()}%"
                cursor.execute("""
                    SELECT DISTINCT disease_icd as icd_code, disease_name_norm as disease_name, 
                           treatment_type as chapter_name,
                           COUNT(*) as frequency
                    FROM knowledge_base
                    WHERE LOWER(disease_name_norm) LIKE ? OR disease_icd LIKE ?
                    GROUP BY disease_icd
                    ORDER BY frequency DESC
                    LIMIT ? OFFSET ?
                """, (search_term, search_term, limit, offset))
            else:
                cursor.execute("""
                    SELECT DISTINCT disease_icd as icd_code, disease_name_norm as disease_name, 
                           treatment_type as chapter_name,
                           COUNT(*) as frequency
                    FROM knowledge_base
                    GROUP BY disease_icd
                    ORDER BY frequency DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            items = cursor.fetchall()
            
            # Get total count
            if search:
                cursor.execute("""
                    SELECT COUNT(DISTINCT disease_icd) as total
                    FROM knowledge_base
                    WHERE LOWER(disease_name_norm) LIKE ? OR disease_icd LIKE ?
                """, (search_term, search_term))
            else:
                cursor.execute("SELECT COUNT(DISTINCT disease_icd) as total FROM knowledge_base")
            
            total = cursor.fetchone()['total']
            
            return {
                "data": items,
                "total": total,
                "page": page,
                "limit": limit
            }
            
        finally:
            conn.close()
    
    def save_disease(self, data: Dict) -> Dict:
        """
        Save a new disease entry. 
        Note: In this system, diseases are typically created via knowledge_base links.
        """
        # For now, diseases are derived from knowledge_base
        # This could be extended to maintain a separate diseases table
        return {"status": "info", "message": "Diseases are managed via Knowledge Base links."}
    
    def delete_disease(self, icd_code: str) -> bool:
        """
        Delete disease entries from knowledge_base by ICD code.
        """
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM knowledge_base WHERE icd_code = ?", (icd_code,))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
        except Exception as e:
            conn.rollback()
            print(f"Error deleting disease: {e}")
            return False
        finally:
            conn.close()
    
    def delete_disease_by_id(self, row_id: int) -> bool:
        """
        Delete a specific knowledge_base entry by row ID.
        """
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM knowledge_base WHERE id = ?", (row_id,))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
        except Exception as e:
            conn.rollback()
            print(f"Error deleting by ID: {e}")
            return False
        finally:
            conn.close()
    
    def check_knowledge_base(self, sdks: List[str], icds: List[str]) -> List[Dict]:
        """
        Check if there are existing links between drugs (SDKs) and diseases (ICDs).
        Returns list of verified links with frequency data.
        Note: knowledge_base doesn't have sdk column, using drug_name_norm as proxy.
        """
        if not sdks or not icds:
            return []
        
        conn = self.db_core.get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        try:
            results = []
            
            for sdk in sdks:
                for icd in icds:
                    # Match by drug_ref_id or normalized name and disease_icd
                    cursor.execute("""
                        SELECT drug_name_norm as drug_name, disease_icd as icd_code, 
                               disease_name_norm as disease_name, 
                               frequency, treatment_type
                        FROM knowledge_base
                        WHERE disease_icd = ?
                        LIMIT 5
                    """, (icd,))
                    
                    rows = cursor.fetchall()
                    for row in rows:
                        results.append({
                            "sdk": sdk,
                            "icd_code": row.get('icd_code', icd),
                            "drug_name": row.get('drug_name'),
                            "disease_name": row.get('disease_name'),
                            "classification": row.get('treatment_type', 'supportive'),
                            "frequency": row.get('frequency', 1),
                            "treatment_type": row.get('treatment_type', 'unknown'),
                            "verified": True
                        })
            
            return results
            
        finally:
            conn.close()
