import pytest
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_consult_kb_hit(client, mock_db_engine):
    """Test Consult with high confidence Internal KB match"""
    # 1. Mock DB Connection & Cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_db_engine.get_connection.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # row_factory lambda in code: lambda c, r: dict...
    # We can perform simple logic or just ensure cursor returns a dict-like object if checking fields
    # But the code uses `row['confidence_score']`. So returning a dict is fine.
    
    # Return high confidence for the loop
    # Query: SELECT frequency, confidence_score ...
    mock_cursor.fetchone.return_value = {"frequency": 100, "confidence_score": 0.95}

    payload = {
        "request_id": "TEST-01",
        "items": [{"id": "d1", "name": "Paracetamol"}],
        "diagnoses": [{"code": "R51", "name": "Headache", "type": "MAIN"}]
    }

    response = await client.post("/api/v1/consult/consult_integrated", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    res = data["results"][0]
    
    assert res["source"] == "INTERNAL_KB"
    assert "95%" in res["explanation"]
    assert res["validity"] == "valid"

@pytest.mark.asyncio
async def test_consult_ai_fallback(client, mock_db_engine, mocker):
    """Test Consult with KB Miss -> AI Fallback"""
    # 1. Mock DB Miss
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_engine.get_connection.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None # No KB entry
    
    # 2. Mock AI Service
    mock_ai = mocker.patch("app.api.consult.analyze_treatment_group")
    mock_ai.return_value = {
        "status": "success",
        "results": [
            {
                "disease": "Headache",
                "medications": [
                    ["Paracetamol (VN-SDK)", "Good for headache"]
                ]
            }
        ]
    }
    
    payload = {
        "request_id": "TEST-02",
        "items": [{"id": "d1", "name": "Paracetamol"}],
        "diagnoses": [{"code": "R51", "name": "Headache", "type": "MAIN"}]
    }

    response = await client.post("/api/v1/consult/consult_integrated", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    res = data["results"][0]
    
    assert res["source"] == "EXTERNAL_AI"
    assert "Good for headache" in res["explanation"]
    assert res["validity"] == "valid"
