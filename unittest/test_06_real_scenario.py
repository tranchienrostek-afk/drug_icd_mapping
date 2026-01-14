import pytest
from unittest.mock import MagicMock

# Golden Data extracted from test_results.json
GOLDEN_DATA = [
  {
    "drug": "Ludox - 200mg",
    "result": {
      "status": "success",
      "data": {
        "official_name": "Ludox",
        "sdk": "VN-5145-16",
        "active_ingredient": "Amisulpride",
        "usage": "Điều trị triệu chứng ở bệnh nhân tâm thần phân liệt.",
        "confidence": 0.9,
        "source_url": "https://trungtamthuoc.com/thuoc/ludox"
      },
      "steps": [
        "Round 1: navigate",
        "Round 2: answer"
      ]
    }
  },
  {
    "drug": "Berodual 200 liều (xịt) - 10ml",
    "result": {
      "status": "success",
      "data": {
        "official_name": "Berodual",
        "sdk": "VD-19804-16",
        "active_ingredient": "Bromhexin Hydrochloride và Ipratropium Bromide",
        "usage": "Chỉ định điều trị bệnh phổi tắc nghẽn mạn tính, hen phế quản",
        "confidence": 0.9,
        "source_url": "https://trungtamthuoc.com/thuoc/berodual"
      },
      "steps": [
        "Round 1: navigate",
        "Round 2: answer"
      ]
    }
  },
  {
    "drug": "Symbicort 120 liều",
    "result": {
      "status": "success",
      "data": {
        "official_name": "Symbicort",
        "sdk": "VN-12345-16",
        "active_ingredient": "Budesonide, Formoterol",
        "usage": "Chỉ định trong điều trị bệnh hen phế quản và COPD.",
        "confidence": 0.9,
        "source_url": "https://trungtamthuoc.com/thuoc/symbicort"
      },
      "steps": [
        "Round 1: navigate",
        "Round 2: answer"
      ]
    }
  }
]

@pytest.mark.asyncio
async def test_agent_search_real_scenarios(client, mock_agent_service):
    """
    Test /agent-search with REAL golden data.
    This ensures the API correctly parses and returns complex real-world responses.
    """
    for entry in GOLDEN_DATA:
        input_drug = entry["drug"]
        golden_response = entry["result"]
        
        # Configure Mock to return the specific golden result for this input
        # Note: Since mock_agent_service is a function mock, we can't easily map input->output 
        # unless we use side_effect with a function.
        
        async def side_effect(query):
            if query == input_drug:
                return golden_response
            return {"status": "error", "message": "Unknown mock input"}
            
        mock_agent_service.side_effect = side_effect
        
        payload = {"drugs": [input_drug]}
        response = await client.post("/api/v1/drugs/agent-search", json=payload)
        
        assert response.status_code == 200
        json_resp = response.json()
        
        # Verify correctness
        assert len(json_resp["results"]) == 1
        result = json_resp["results"][0]
        

        assert result["data"]["official_name"] == golden_response["data"]["official_name"]
        assert result["data"]["sdk"] == golden_response["data"]["sdk"]
        assert result["data"]["active_ingredient"] == golden_response["data"]["active_ingredient"]
