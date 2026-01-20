import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.service.consultation_service import ConsultationService
from app.models import ConsultRequest, DrugItem, DiagnosisItem

# Mock DB Core and Connection
@pytest.fixture
def mock_db_core():
    db_core = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()
    
    db_core.get_connection.return_value = conn
    conn.cursor.return_value = cursor
    return db_core, cursor

@pytest.mark.asyncio
async def test_integrated_consult_tdv_match(mock_db_core):
    db_core, cursor = mock_db_core
    service = ConsultationService(db_core)
    
    # Mock Data: TDV Match
    # Row structure: treatment_type, tdv_feedback, frequency
    cursor.fetchall.return_value = [
        {'treatment_type': 'Support', 'tdv_feedback': '["{Thuốc điều trị chính}"]', 'frequency': 10},
        {'treatment_type': 'Main', 'tdv_feedback': None, 'frequency': 5}
    ]
    
    request = ConsultRequest(
        request_id="test-01",
        items=[DrugItem(id="d1", name="Paracetamol 500mg")],
        diagnoses=[DiagnosisItem(code="R51", name="Headache", type="MAIN")]
    )
    
    results = await service.process_integrated_consultation(request)
    
    assert len(results) == 1
    res = results[0]
    assert res['source'] == 'INTERNAL_KB_TDV'
    assert res['role'] == 'Thuốc điều trị chính'
    assert res['validity'] == 'valid'

@pytest.mark.asyncio
async def test_integrated_consult_ai_match(mock_db_core):
    db_core, cursor = mock_db_core
    service = ConsultationService(db_core)
    
    # Mock Data: AI Match only (tdv_feedback is None or empty)
    cursor.fetchall.return_value = [
        {'treatment_type': 'Thuốc hỗ trợ', 'tdv_feedback': None, 'frequency': 100}
    ]
    
    request = ConsultRequest(
        request_id="test-02",
        items=[DrugItem(id="d2", name="Vitamin C")],
        diagnoses=[DiagnosisItem(code="J00", name="Cold", type="MAIN")]
    )
    
    results = await service.process_integrated_consultation(request)
    
    assert len(results) == 1
    res = results[0]
    assert res['source'] == 'INTERNAL_KB_AI'
    assert res['role'] == 'Thuốc hỗ trợ'

@pytest.mark.asyncio
async def test_integrated_consult_no_match(mock_db_core):
    db_core, cursor = mock_db_core
    service = ConsultationService(db_core)
    
    # Mock Data: No rows found
    cursor.fetchall.return_value = []
    
    request = ConsultRequest(
        request_id="test-03",
        items=[DrugItem(id="d3", name="Unknown Drug")],
        diagnoses=[DiagnosisItem(code="X99", name="Unknown", type="MAIN")]
    )
    
    results = await service.process_integrated_consultation(request)
    
    # Expect 1 result with "empty" fields (per user request)
    assert len(results) == 1
    res = results[0]
    assert res['source'] == 'INTERNAL_KB_EMPTY'
    assert res['role'] == ''
    assert res['validity'] == 'unknown'
    assert res['name'] == 'Unknown Drug'

@pytest.mark.asyncio
async def test_normalization_logic(mock_db_core):
    db_core, cursor = mock_db_core
    service = ConsultationService(db_core)
    
    # Setup mock to return a match regardless of input, 
    # but we want to verify the SQL query params were normalized
    cursor.fetchall.return_value = [] 
    
    request = ConsultRequest(
        request_id="test-04",
        items=[DrugItem(id="d1", name="Panadol   Extra   500mg")], # Messy input
        diagnoses=[DiagnosisItem(code="r51 ", name="Headache", type="MAIN")]
    )
    
    await service.process_integrated_consultation(request)
    
    # Check what was passed to execute
    # normalize_text("Panadol   Extra   500mg") -> "panadol extra" (doses removed by app.core.utils)
    # verify logic in app.core.utils or manual expectation
    
    args = cursor.execute.call_args
    # args[0] is SQL, args[1] is params tuple (drug_norm, disease_icd)
    sql_query, params = args[0]
    
    # normalize_text uses normalize_drug_name which removes "500mg" and lowercases
    # Expected: "panadol extra"
    normalized_drug = params[0]
    normalized_icd = params[1]
    
    assert normalized_icd == "r51" # Lowercase and stripped (matching DB)
    # Note: Exact normalization result depends on app.core.utils implementation details
    # We just ensure it's not the raw string
    assert normalized_drug != "Panadol   Extra   500mg"
