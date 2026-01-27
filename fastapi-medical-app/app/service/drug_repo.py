import sqlite3
from app.database.core import DatabaseCore

class DrugRepository:
    def __init__(self, db_core: DatabaseCore = None):
        if db_core is None:
            self.db_core = DatabaseCore()
        else:
            self.db_core = db_core

    async def get_drug_by_id(self, row_id):
        conn = self.db_core.get_connection()
        # conn.row_factory = sqlite3.Row # Moved to core or handled by cursor_factory
        cursor = conn.cursor()
        try:
            # Use 'id' instead of 'rowid' which is standard across SQLite and Postgres
            cursor.execute("SELECT id, * FROM drugs WHERE id = ?", (row_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_all_drugs(self, page=1, limit=10, search=None):
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        offset = (page - 1) * limit
        try:
            if search:
                search_term = f"%{search.strip()}%"
                cursor.execute("SELECT count(*) FROM drugs WHERE ten_thuoc LIKE ? OR so_dang_ky LIKE ?", (search_term, search_term))
                # Handle different cursor return types (tuple vs dict)
                res = cursor.fetchone()
                # If RealDictCursor (Postgres), it returns dict. If tuple (SQLite default), tuple.
                # However, our core wrapper for SQLite uses dict_factory.
                # If Postgres RealDictCursor, 'count(*)' might be accessed via key or list?
                # RealDictCursor returns {'count': 123} usually if named, or just verify access.
                # Best compatibility: use aliases
                
                # Check DB Type to be safe or use alias provided by logic
                if isinstance(res, dict):
                    # Postgres RealDictCursor or SQLite dict_factory
                    # count(*) usually comes as 'count'
                    total = list(res.values())[0]
                else:
                    total = res[0]
                
                cursor.execute("""
                    SELECT id, * FROM drugs 
                    WHERE ten_thuoc LIKE ? OR so_dang_ky LIKE ?
                    ORDER BY ten_thuoc LIMIT ? OFFSET ?
                """, (search_term, search_term, limit, offset))
            else:
                cursor.execute("SELECT count(*) FROM drugs")
                res = cursor.fetchone()
                if isinstance(res, dict):
                    total = list(res.values())[0]
                else:
                    total = res[0]
                
                cursor.execute("SELECT id, * FROM drugs ORDER BY updated_at DESC LIMIT ? OFFSET ?", (limit, offset))
            
            rows = cursor.fetchall()
            return {"data": [dict(r) for r in rows], "total": total, "page": page, "limit": limit}
        finally:
            conn.close()

    def delete_drug(self, sdk: str) -> bool:
        """Delete drug by Số Đăng Ký (SDK)."""
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            # Also delete from FTS if exists (SQLite Only)
            if self.db_core.db_type == 'sqlite':
                cursor.execute("SELECT id FROM drugs WHERE so_dang_ky = ?", (sdk,))
                row = cursor.fetchone()
                if row:
                    # Dict or Tuple check
                    row_id = row['id'] if isinstance(row, dict) else row[0]
                    cursor.execute("DELETE FROM drugs_fts WHERE rowid = ?", (row_id,))
            
            cursor.execute("DELETE FROM drugs WHERE so_dang_ky = ?", (sdk,))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
        except Exception as e:
            conn.rollback()
            print(f"Error deleting drug: {e}")
            return False
        finally:
            conn.close()

    def delete_drug_by_id(self, row_id: int) -> bool:
        """Delete drug by row ID."""
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            # Delete from FTS (SQLite Only)
            if self.db_core.db_type == 'sqlite':
                cursor.execute("DELETE FROM drugs_fts WHERE rowid = ?", (row_id,))
            
            # Delete from main table
            cursor.execute("DELETE FROM drugs WHERE id = ?", (row_id,))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
        except Exception as e:
            conn.rollback()
            print(f"Error deleting drug by ID: {e}")
            return False
        finally:
            conn.close()

    def get_links_list(self, page: int = 1, limit: int = 20, search: str = "") -> dict:
        """Get paginated list of drug-disease links from knowledge_base."""
        conn = self.db_core.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        offset = (page - 1) * limit
        
        try:
            if search:
                search_term = f"%{search.strip()}%"
                cursor.execute("""
                    SELECT COUNT(*) FROM knowledge_base 
                    WHERE (drug_name_norm LIKE ? OR disease_name_norm LIKE ? OR disease_icd LIKE ?)
                    AND drug_name_norm != '_icd_list_'
                """, (search_term, search_term, search_term))
                total = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT id, drug_ref_id, disease_icd as icd_code, 
                           drug_name_norm as drug_name, disease_name_norm as disease_name, 
                           treatment_type as phan_loai, frequency,
                           tdv_feedback, symptom, prescription_reason,
                           secondary_disease_icd, secondary_disease_name
                    FROM knowledge_base
                    WHERE (drug_name_norm LIKE ? OR disease_name_norm LIKE ? OR disease_icd LIKE ?)
                    AND drug_name_norm != '_icd_list_'
                    ORDER BY frequency DESC
                    LIMIT ? OFFSET ?
                """, (search_term, search_term, search_term, limit, offset))
            else:
                cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE drug_name_norm != '_icd_list_'")
                total = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT id, drug_ref_id, disease_icd as icd_code, 
                           drug_name_norm as drug_name, disease_name_norm as disease_name, 
                           treatment_type as phan_loai, frequency,
                           tdv_feedback, symptom, prescription_reason,
                           secondary_disease_icd, secondary_disease_name
                    FROM knowledge_base
                    WHERE drug_name_norm != '_icd_list_'
                    ORDER BY frequency DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            rows = cursor.fetchall()
            return {"data": [dict(r) for r in rows], "total": total, "page": page, "limit": limit}
        finally:
            conn.close()

    def delete_link(self, sdk: str, icd_code: str) -> bool:
        """Delete a drug-disease link from knowledge_base (by disease_icd)."""
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            # Note: We don't have sdk in knowledge_base, so we match by disease_icd only
            cursor.execute("DELETE FROM knowledge_base WHERE disease_icd = ?", (icd_code,))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
        except Exception as e:
            conn.rollback()
            print(f"Error deleting link: {e}")
            return False
        finally:
            conn.close()

