"""
Pytest Configuration for Medical API Test Suite
================================================
- Provides test database isolation
- Auto-cleanup of test data
- Mock fixtures for external services
"""

import pytest
import os
import sys
import shutil
import sqlite3
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock

# Path setup for Docker
if os.path.exists("/app"):
    UNITTEST_DIR = "/app"
    APP_DIR = "/app"
    TEST_DB_PATH = "/app/test_medical.db"
    PROD_DB_PATH = "/app/app/database/medical.db"
    sys.path.insert(0, "/app")
else:
    # Original local paths
    UNITTEST_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = os.path.join(UNITTEST_DIR, "..", "fastapi-medical-app")
    TEST_DB_PATH = os.path.join(UNITTEST_DIR, "test_medical.db")
    PROD_DB_PATH = os.path.join(APP_DIR, "app", "database", "medical.db")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fastapi-medical-app")))

# Set ENV for testing BEFORE importing app
os.environ["TESTING"] = "True"
os.environ["DB_PATH"] = TEST_DB_PATH
os.environ["AZURE_OPENAI_KEY"] = "test-key-mock"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "test-deployment"


@pytest.fixture(scope="session")
def setup_test_db():
    """
    Session-scope fixture: Copy production DB to test DB at start.
    This ensures tests have realistic data to work with.
    """
    print(f"\n🔧 Setting up test database: {TEST_DB_PATH}")
    
    if os.path.exists(PROD_DB_PATH):
        try:
            shutil.copy(PROD_DB_PATH, TEST_DB_PATH)
            print(f"✅ Copied production DB to test DB")
        except Exception as e:
            print(f"⚠️ Failed to copy DB: {e}")
            from app.database.core import DatabaseCore
            DatabaseCore(TEST_DB_PATH)
    else:
        print(f"⚠️ Production DB not found at {PROD_DB_PATH}, will create new schema")
        from app.database.core import DatabaseCore
        DatabaseCore(TEST_DB_PATH)
    
    yield TEST_DB_PATH
    
    # Cleanup after all tests complete
    print("\n🧹 Test session completed. Test database preserved for inspection.")


@pytest.fixture(scope="session")
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def client(setup_test_db):
    """Create async test client."""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_db_engine(mocker):
    """Mock DrugDbEngine for unit tests that don't need real DB."""
    try:
        from app.services import DrugDbEngine
        mock_instance = MagicMock(spec=DrugDbEngine)
        
        mocker.patch("app.api.drugs.db", mock_instance)
        mocker.patch("app.api.consult.db", mock_instance)
        mocker.patch("app.api.analysis.db", mock_instance)
        mocker.patch("app.api.data_management.db", mock_instance)
        
        return mock_instance
    except ImportError:
        return MagicMock()


@pytest.fixture
def mock_agent_service(mocker):
    """Mock the run_agent_search function."""
    mock_result = {
        "drug_name": "Test Drug",
        "status": "found",
        "data": {"so_dang_ky": "TEST-SDK"}
    }
    # Handle module path changes if needed
    try:
        return mocker.patch("app.api.drugs.run_agent_search", return_value=mock_result)
    except Exception:
        return MagicMock()


@pytest.fixture
def mock_openai(mocker):
    """Mock AzureOpenAI client for AI-related tests."""
    import json
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "analysis": "Mocked AI analysis",
        "recommendations": ["Mocked recommendation"]
    })
    
    mock_client = mocker.MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    try:
        mocker.patch("app.service.ai_consult_service.get_openai_client", return_value=mock_client)
        mocker.patch("app.services.get_openai_client", return_value=mock_client)
    except Exception:
        pass
        
    return mock_client


def pytest_configure(config):
    """Pytest hook: Configure markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
