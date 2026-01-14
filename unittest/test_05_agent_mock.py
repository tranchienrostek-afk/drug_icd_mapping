import pytest
from unittest.mock import MagicMock, AsyncMock
import json

@pytest.mark.asyncio
async def test_agent_search_service_logic(mocker):
    """Test run_agent_search service logic with mocked OpenAI"""
    
    # Mock imports in service
    mock_openai_class = mocker.patch("app.service.agent_search_service.AsyncAzureOpenAI")
    mock_client = AsyncMock()
    mock_openai_class.return_value = mock_client
    
    # Mock Playwright Manager (used in service)
    mock_pw = MagicMock()
    mocker.patch("app.service.agent_search_service.PlaywrightManager", return_value=mock_pw)
    # mock_pw.start_browser is async
    mock_pw.start_browser = AsyncMock()
    mock_pw.stop_browser = AsyncMock()
    mock_pw.navigate_to_url = AsyncMock()
    mock_pw.navigate_to_url.return_value = ("http://test", "<html>DOM</html>", [])
    mock_pw.get_dom_content = AsyncMock()
    mock_pw.get_dom_content.return_value = "DOM Content"
    
    # Prepare Mock LLM Responses for a 2-step flow:
    # Round 1: Search -> Navigate
    # Round 2: Answer
    
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock()]
    mock_response_1.choices[0].message.content = json.dumps({
        "thought": "Searching",
        "action": "navigate",
        "url": "http://drug.com"
    })
    
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock()]
    mock_response_2.choices[0].message.content = json.dumps({
        "thought": "Found info",
        "action": "answer",
        "official_name": "Test Drug",
        "status": "success",
        "data": {
            "official_name": "Test Drug",
            "sdk": "VN-TEST",
            "active_ingredient": "Test",
            "usage": "Test Usage",
            "confidence": 0.9,
            "source_url": "http://drug.com"
        }
    })
    
    # Configure side_effect for multiple calls
    mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
    
    from app.service.agent_search_service import run_agent_search
    
    result = await run_agent_search("Test Drug")
    
    assert result["status"] == "success"
    assert result["data"]["official_name"] == "Test Drug"
    assert result["rounds"] == 2
