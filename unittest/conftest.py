import pytest
import os
import sys
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fastapi-medical-app")))

# Set ENV for testing
os.environ["TESTING"] = "True"
os.environ["AZURE_OPENAI_KEY"] = "test-key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-05-15"
os.environ["DB_PATH"] = ":memory:"

from app.main import app
from app.services import DrugDbEngine

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def client():
    # Use ASGITransport for direct app testing without running server
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
def mock_db_engine(mocker):
    """
    Mock entire DrugDbEngine to avoid real DB calls.
    We mock the `app.api.drugs.db` instance, etc.
    However, since `db` is instantiated globally in api files, we need to patch wherever it's imported.
    """
    mock_instance = MagicMock(spec=DrugDbEngine)
    
    # Patch the global 'db' object in different modules
    mocker.patch("app.api.drugs.db", mock_instance)
    mocker.patch("app.api.consult.db", mock_instance)
    mocker.patch("app.api.analysis.db", mock_instance) # If analysis uses it
    mocker.patch("app.api.data_management.db", mock_instance)
    
    return mock_instance

@pytest.fixture
def mock_agent_service(mocker):
    """Mock the run_agent_search function"""
    return mocker.patch("app.api.drugs.run_agent_search")

@pytest.fixture
def mock_openai(mocker):
    """Mock AzureOpenAI client"""
    return mocker.patch("app.service.agent_search_service.AsyncAzureOpenAI")
