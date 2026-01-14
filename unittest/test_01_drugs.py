import pytest
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_identify_drug_db_match(client, mock_db_engine):
    """Test /identify when drug is found in DB (Verified)"""
    # Setup Mock
    mock_db_engine.search_drug_smart.return_value = {
        "data": {
            "ten_thuoc": "Paracetamol",
            "so_dang_ky": "VN-12345",
            "hoat_chat": "Paracetamol",
            "is_verified": 1,
            "classification": "OTC"
        },
        "confidence": 1.0,
        "source": "Database (Exact)"
    }
    
    payload = {"drugs": ["Paracetamol 500mg"]}
    response = await client.post("/api/v1/drugs/identify", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    result = data["results"][0]
    
    assert result["input_name"] == "Paracetamol 500mg"
    assert result["db_match"] is True
    assert result["official_name"] == "Paracetamol"
    assert result["sdk"] == "VN-12345"

@pytest.mark.asyncio
async def test_identify_drug_not_found(client, mock_db_engine, mocker):
    """Test /identify when not in DB (Fallbacks to Web Crawler)"""
    # Mock DB Miss
    mock_db_engine.search_drug_smart.return_value = None
    
    # Mock Crawler
    mock_crawler = mocker.patch("app.api.drugs.scrape_drug_web")
    mock_crawler.return_value = {
        "ten_thuoc": "New Drug",
        "so_dang_ky": "VN-NEW",
        "hoat_chat": "New Ingredient",
        "source": "Web",
        "confidence": 0.8
    }
    
    payload = {"drugs": ["New Drug"]}
    response = await client.post("/api/v1/drugs/identify", json=payload)
    
    assert response.status_code == 200
    result = response.json()["results"][0]
    
    assert result["db_match"] is False
    assert result["official_name"] == "New Drug"
    assert result["source"] == "Web"

@pytest.mark.asyncio
async def test_agent_search_endpoint(client, mock_agent_service):
    """Test /agent-search endpoint"""
    # Setup Mock
    mock_agent_service.return_value = {
        "status": "success",
        "data": {"official_name": "Agent Drug"},
        "rounds": 2
    }
    
    payload = {"drugs": ["Complex Drug"]}
    response = await client.post("/api/v1/drugs/agent-search", json=payload)
    
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["data"]["official_name"] == "Agent Drug"
    mock_agent_service.assert_called_once_with("Complex Drug")

@pytest.mark.asyncio
async def test_get_all_drugs(client, mock_db_engine):
    """Test GET /drugs/ (Pagination)"""
    mock_db_engine.get_all_drugs.return_value = {
        "data": [{"id": 1, "ten_thuoc": "A"}],
        "total": 1,
        "page": 1,
        "limit": 10
    }
    
    response = await client.get("/api/v1/drugs/?page=1&limit=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1
