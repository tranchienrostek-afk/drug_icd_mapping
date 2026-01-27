import pytest
import asyncio
from unittest.mock import MagicMock, patch

# Import logic (handle path differences)
try:
    from app.service.consultation_service import ConsultationService
    from app.models import ConsultRequest, DrugItem, DiagnosisItem
except ImportError:
    import sys
    import os
    sys.path.append(os.getcwd())
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
    
    # We need to mock the sequence of DB calls done by KBFuzzyMatchService
    # 1. find_best_match -> Exact match query -> fetchone()
    # 2. find_best_match_with_icd -> KB lookup query -> fetchone()
    
    # Mock Row 1: Exact match found for drug name
    row1 = {'drug_name_norm': 'paracetamol 500mg'}
    
    # Mock Row 2: KB Data found
    row2 = {
        'drug_name_norm': 'paracetamol 500mg',
        'disease_icd': 'r51',
        'treatment_type': 'Support', 
        'tdv_feedback': '["{Thuốc điều trị chính}"]', 
        'frequency': 10
    }
    
    # Set side_effect. 
    # Note: cursor.fetchone() might be called more times if logic changes, 
    # but based on current code:
    # - find_best_match(exact) -> returns row1 -> returns match
    # - find_best_match_with_icd(lookup) -> returns row2
    cursor.fetchone.side_effect = [row1, row2]
    
    request = ConsultRequest(
        request_id="test-01",
        items=[DrugItem(id="d1", name="Paracetamol 500mg")],
        diagnoses=[DiagnosisItem(code="R51", name="Headache", type="MAIN")]
    )
    
    results = await service.process_integrated_consultation(request)
    
    assert len(results) == 1
    res = results[0]
    assert res['source'] == 'INTERNAL_KB_TDV'
    # Flexible assertion for role
    assert 'Thuốc điều trị chính' in res['role']
    assert res['validity'] == 'valid'

@pytest.mark.asyncio
async def test_integrated_consult_ai_match(mock_db_core):
    db_core, cursor = mock_db_core
    service = ConsultationService(db_core)
    
    # Sequence:
    # 1. Exact match -> Found
    # 2. KB lookup -> Found AI data
    
    row1 = {'drug_name_norm': 'vitamin c'}
    row2 = {
        'drug_name_norm': 'vitamin c',
        'disease_icd': 'j00',
        'treatment_type': 'Thuốc hỗ trợ', 
        'tdv_feedback': None, 
        'frequency': 100
    }
    
    cursor.fetchone.side_effect = [row1, row2]
    
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
    
    # Sequence for NO MATCH:
    # 1. Exact match -> None
    # 2. Like match -> None
    # 3. Fuzzy/TFIDF -> Load cache (fetchall) -> Perform calculation -> None (if lists empty/no match)
    
    # Mocking behaviors:
    cursor.fetchone.return_value = None # All fetchone calls return None
    
    # Mock fetchall for cache loading (if triggered). Return empty list or minimal list
    cursor.fetchall.return_value = [] 
    
    # Need to verify if 'drug_names' in service is empty, RapidFuzz won't match.
    # Service expects fetchall to return [(name,), ...]
    
    request = ConsultRequest(
        request_id="test-03",
        items=[DrugItem(id="d3", name="Unknown Drug")],
        diagnoses=[DiagnosisItem(code="X99", name="Unknown", type="MAIN")]
    )
    
    results = await service.process_integrated_consultation(request)
    
    # Expect 1 result with "empty" fields
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
    
    # Just need to check the call arguments.
    # We can make it return None to exit early, but we want to capture the first execute call.
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    
    request = ConsultRequest(
        request_id="test-04",
        items=[DrugItem(id="d1", name="Panadol   Extra   500mg")],
        diagnoses=[DiagnosisItem(code="r51 ", name="Headache", type="MAIN")]
    )
    
    await service.process_integrated_consultation(request)
    
    # process_integrated_consultation -> find_best_match_with_icd -> find_best_match
    # find_best_match calls execute() for Exact Match first.
    
    # Verify execute was called
    assert cursor.execute.called
    
    # Inspect arguments of the FIRST call (Exact Match)
    args = cursor.execute.call_args_list[0]
    # args[0] is (sql, params)
    sql_query, params = args[0]
    
    normalized_drug_arg = params[0]
    
    # normalize_for_matching is used. It lowercases.
    # "Panadol   Extra   500mg" -> "panadol extra 500mg" (depending on util)
    # Just assert it is NOT the raw string
    assert normalized_drug_arg != "Panadol   Extra   500mg"
    assert "panadol" in normalized_drug_arg
