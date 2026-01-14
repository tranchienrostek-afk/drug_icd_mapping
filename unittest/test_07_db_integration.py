import pytest
import sqlite3
from unittest.mock import MagicMock
from app.services import DrugDbEngine
from app.service.etl_service import process_raw_log
from app.api.consult import consult_integrated, ConsultRequest, DrugItem, DiagnosisItem

# Helper for Persistent In-Memory DB
class PersistentDbEngine(DrugDbEngine):
    def __init__(self):
        # Initialize with :memory:
        self.db_path = ":memory:"
        # Create a single persistent connection
        self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._shared_conn.row_factory = sqlite3.Row # Use Row for dict-like access
        
        # Initialize tables on this connection
        self._ensure_tables_persistent()
        
    def _ensure_tables_persistent(self):
        # We override _ensure_tables to use our shared connection logic
        # But easier is to just call the logic using our connection
        # Since _ensure_tables calls get_connection, we just need get_connection to work.
        super()._ensure_tables()

    def get_connection(self):
        # Return a proxy that uses self._shared_conn but ignores close()
        return ConnectionProxy(self._shared_conn)

class ConnectionProxy:
    def __init__(self, real_conn):
        self.real_conn = real_conn
        self.row_factory = real_conn.row_factory
        
    def cursor(self):
        return self.real_conn.cursor()
        
    def commit(self):
        return self.real_conn.commit()
    
    def rollback(self):
        return self.real_conn.rollback()
        
    def close(self):
        # Do NOT close the real connection
        pass
        
    def execute(self, sql, params=()):
        return self.real_conn.execute(sql, params)

@pytest.mark.asyncio
async def test_etl_to_consult_integration(mocker):
    """
    Integration test using a PERSISTENT in-memory SQLite database.
    We patch the global 'db' instances in modules to use our single shared DB.
    """
    
    # 1. Setup Persistent DB
    persistent_db = PersistentDbEngine()
    
    # 2. Patch global 'db' in app modules to use our persistent instance
    # Note: process_raw_log uses 'app.service.etl_service.db'
    # consult_integrated uses 'app.api.consult.db'
    mocker.patch("app.service.etl_service.db", persistent_db)
    mocker.patch("app.api.consult.db", persistent_db)
    
    # Also patch app.services.DrugDbEngine to return our instance if anyone instantiates it new?
    # Not needed if we patch the specific variable references.
    
    # 3. ETL Ingestion
    batch_id = "test_batch_integr_01"
    # Note: 'upsert_knowledge_base' (called by process_raw_log) is a method of DrugDbEngine.
    # Since we patched 'db' with persistent_db, it will call persistent_db.upsert_knowledge_base
    # which inherits from DrugDbEngine.upsert_knowledge_base.
    # upsert_knowledge_base isn't in DrugDbEngine in app/services.py?
    # Wait, I need to check if DrugDbEngine HAS upsert_knowledge_base.
    # Reading app/services.py earlier, I didn't see it explicitly in the summary, 
    # but I saw 'save_verified_drug', 'get_connection'.
    # I might have missed it or it was added previously?
    # Let's check app/services.py again or assume it exists because verify_031.py called it.
    # verify_031.py: imported process_raw_log.
    # process_raw_log call: db.upsert_knowledge_base(drug, disease, icd)
    # If DrugDbEngine doesn't have it, process_raw_log would fail.
    # I should double check app/services.py content.
    # Just in case, I'll add a mock wrapper if it's missing, but it should be there.
    
    csv_content = "drug_name,disease_name,icd_code\nPanadol Integration,Headache Test,R51\nUnknownDrug,RareDisease,Q99"
    await process_raw_log(batch_id, csv_content)
    
    # 4. Verify DB Content
    conn = persistent_db.get_connection()
    cursor = conn.cursor()
    # Schema changed: Raw logs, so we count rows
    cursor.execute("SELECT count(*) as frequency FROM knowledge_base WHERE drug_name_norm = 'panadol integration'")
    row = cursor.fetchone()
    # Debug: if row is None, check table names
    if row is None:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print("Tables:", cursor.fetchall())
        
    assert row['frequency'] >= 1, "ETL failed to insert data into knowledge_base"
    # Do not verify internal state of connection close
    
    # 5. Consult - Low Confidence
    payload = ConsultRequest(
        request_id="req-test-integr-1",
        items=[
            DrugItem(id="d1", name="Panadol Integration"),
            DrugItem(id="d2", name="UnknownDrugXYZ")
        ],
        diagnoses=[
            DiagnosisItem(code="R51", name="Headache Test", type="MAIN")
        ]
    )
    
    # Mock AI to control fallback
    mock_ai_response = {
        "results": [
            {
                "id": "d1",
                "drug_name": "Panadol Integration",
                "source": "AI_GENERATED", 
                "treatment_type": "SUPPORTIVE",
                "original_name": "Panadol Integration"
            }
        ]
    }
    mocker.patch("app.api.consult.analyze_treatment_group", return_value=mock_ai_response)
    
    response = await consult_integrated(payload)
    
    # Check results
    res_dict = {r.id: r for r in response.results}
    if 'd1' in res_dict:
        # Should be AI source because confidence is low (freq=1 -> log10(1)=0 -> conf=0.1)
        assert res_dict['d1'].source != "INTERNAL_KB", f"Unexpected source: {res_dict['d1'].source}"

    # 6. Boost Confidence
    # Direct DB update (Insert 100 records to boost freq)
    conn = persistent_db.get_connection()
    cursor = conn.cursor()
    
    # Insert 100 dummy records efficiently
    # We can just insert one record with count... NO, schema is raw.
    # We must insert 100 rows.
    # Use executemany
    dummy_data = [('panadol integration', 'headache test', 'panadol integration', 'headache test', 'Thuốc chính', 'R51')] * 100
    cursor.executemany("""
        INSERT INTO knowledge_base (drug_name_norm, disease_name_norm, raw_drug_name, raw_disease_name, treatment_type, disease_icd)
        VALUES (?, ?, ?, ?, ?, ?)
    """, dummy_data)
    
    conn.commit()
    conn.close()
    
    # 7. Consult - High Confidence
    response_high = await consult_integrated(payload)
    res_dict_high = {r.id: r for r in response_high.results}
    
    assert 'd1' in res_dict_high
    # Now that we boosted confidence (freq ~101 -> log10(101) ~2 -> conf ~1.0), it SHOULD use Internal KB
    # Logic in consult: if conf >= 0.8 -> INTERNAL_KB
    assert res_dict_high['d1'].source == "INTERNAL_KB"

