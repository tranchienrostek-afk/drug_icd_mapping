import pytest
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_treatment_analysis_flow(client, mock_db_engine, mocker):
    """Test full Treatment Analysis flow"""
    
    # 1. Mock Identify Drugs
    mock_identify = mocker.patch("app.api.analysis.identify_drugs")
    mock_identify.return_value = {
        "results": [
            {"input_name": "Para", "official_name": "Paracetamol", "sdk": "VN-1", "db_match": True}
        ]
    }
    
    # 2. Mock Lookup Diseases
    mock_lookup = mocker.patch("app.api.analysis.lookup_diseases")
    mock_lookup.return_value = {
        "results": [
            {"input_diagnosis": "Headache", "icd_code": "R51", "official_name": "Headache"}
        ]
    }
    
    # 3. Mock DB KB Check
    # This calls db.check_knowledge_base(sdks, icds)
    mock_db_engine.check_knowledge_base.return_value = [
        {"sdk": "VN-1", "icd": "R51", "confidence": 0.9}
    ]
    
    # 4. Mock AI Analysis
    mock_analyze = mocker.patch("app.api.analysis.analyze_treatment_group")
    mock_analyze.return_value = {
        "status": "success",
        "results": [{"disease": "Headache", "medications": [["Paracetamol", "OK"]]}]
    }
    
    payload = {
        "drugs": ["Para"],
        "diagnosis": [{"name": "Headache", "icd10": "R51"}]
    }
    
    response = await client.post("/api/v1/analysis/treatment-analysis", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert len(data["drugs_info"]) == 1
    assert data["drugs_info"][0]["official_name"] == "Paracetamol"
    
    assert len(data["diseases_info"]) == 1
    assert data["diseases_info"][0]["icd_code"] == "R51"
    
    assert data["ai_analysis"]["status"] == "success"
    
    # Verify calls
    mock_db_engine.check_knowledge_base.assert_called_with(["VN-1"], ["R51"])
    mock_analyze.assert_called_once()
