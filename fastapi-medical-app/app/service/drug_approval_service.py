import sqlite3
from datetime import datetime
from app.database.core import DatabaseCore
from app.core.utils import normalize_text

class DrugApprovalService:
    def __init__(self, db_core: DatabaseCore = None):
        if db_core is None:
            self.db_core = DatabaseCore()
        else:
            self.db_core = db_core

    def _update_fts(self, cursor, row_id, ten, hoat_chat, cong_ty, search_text):
        cursor.execute("DELETE FROM drugs_fts WHERE rowid = ?", (row_id,))
        cursor.execute("""
            INSERT INTO drugs_fts(rowid, ten_thuoc, hoat_chat, cong_ty_san_xuat, search_text)
            VALUES (?, ?, ?, ?, ?)
        """, (row_id, ten, hoat_chat, cong_ty, search_text))

    def save_verified_drug(self, drug_data):
        conn = self.db_core.get_connection()
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

            if sdk and sdk != 'N/A' and sdk != 'Web Result':
                cursor.execute("SELECT rowid, ten_thuoc FROM drugs WHERE so_dang_ky = ?", (sdk,))
                row = cursor.fetchone()
                if row:
                    conflict_id = row['rowid']
                    conflict_type = 'sdk'
            
            if not conflict_id and ten:
                cursor.execute("SELECT rowid FROM drugs WHERE ten_thuoc = ?", (ten,))
                row = cursor.fetchone()
                if row:
                    conflict_id = row['rowid']
                    conflict_type = 'name'

            # 2. Handle Logic
            if conflict_id:
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
                sql_insert = """
                    INSERT INTO drugs (
                        ten_thuoc, hoat_chat, cong_ty_san_xuat, so_dang_ky, chi_dinh, 
                        tu_dong_nghia, is_verified, search_text, created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """
                cursor.execute(sql_insert, (ten, hoat_chat, cong_ty, sdk, chi_dinh, tu_dong_nghia, search_text, user, now, now))
                row_id = cursor.lastrowid
                
                self._update_fts(cursor, row_id, ten, hoat_chat, cong_ty, search_text)
                
                conn.commit()
                return {"status": "success", "message": f"Saved new drug: {ten} ({sdk})"}

        except sqlite3.Error as e:
            print(f"DB Save Error: {e}")
            conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    def get_pending_stagings(self):
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM drug_staging WHERE status = 'pending' ORDER BY id DESC")
            stagings = cursor.fetchall()
            
            for item in stagings:
                if item.get('conflict_id'):
                    cursor.execute("SELECT ten_thuoc, so_dang_ky, hoat_chat FROM drugs WHERE rowid = ?", (item['conflict_id'],))
                    conflict_drug = cursor.fetchone()
                    item['conflict_info'] = conflict_drug if conflict_drug else None
                else:
                    item['conflict_info'] = None
            
            return stagings
        finally:
            conn.close()

    def approve_staging(self, staging_id, user):
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM drug_staging WHERE id = ?", (staging_id,))
            staging = cursor.fetchone()
            if not staging:
                return {"status": "error", "message": "Staging record not found"}

            conflict_id = staging['conflict_id']
            
            if conflict_id:
                cursor.execute("SELECT * FROM drugs WHERE rowid = ?", (conflict_id,))
                current_drug = cursor.fetchone()
                
                if not current_drug:
                    return {"status": "error", "message": f"Original drug with ID {conflict_id} not found. Cannot merge."}

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
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM drug_staging WHERE id = ?", (staging_id,))
            staging = cursor.fetchone()
            if not staging:
                return {"status": "error", "message": "Staging record not found"}

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

            cursor.execute("UPDATE drug_disease_links SET status='archived' WHERE sdk=? AND status='pending'", (staging['so_dang_ky'],))

            cursor.execute("DELETE FROM drug_staging WHERE id = ?", (staging_id,))
            conn.commit()
            return {"status": "success", "message": "Staging rejected and moved to history."}
        finally:
            conn.close()

    def clear_all_staging(self, user="system"):
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM drug_staging WHERE status = 'pending'")
            items = cursor.fetchall()
            
            if not items:
                return {"status": "success", "message": "No pending items to clear."}

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
        conn = self.db_core.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE drug_staging
                SET ten_thuoc=?, hoat_chat=?, cong_ty_san_xuat=?, so_dang_ky=?, 
                    chi_dinh=?, tu_dong_nghia=?, classification=?, note=?,
                    search_text=?
                WHERE id=?
            """
            cursor.execute(sql, (
                data.get('ten_thuoc'), data.get('hoat_chat'), data.get('cong_ty_san_xuat'),
                data.get('so_dang_ky'), data.get('chi_dinh'), data.get('tu_dong_nghia'),
                data.get('classification'), data.get('note'),
                data.get('search_text'),
                staging_id
            ))
            conn.commit()
            return {"status": "success", "message": "Staging updated."}
        except sqlite3.Error as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
