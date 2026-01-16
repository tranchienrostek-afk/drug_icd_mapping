
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("1. Importing app.api.drugs...")
    from app.api.drugs import router, identification_service
    print("✅ app.api.drugs imported successfully.")

    print("2. Testing DrugIdentificationService instantiation...")
    assert identification_service is not None
    print("✅ identification_service is present in API module.")

    print("3. Testing process_batch (Mocked)...")
    
    # Mock the search service inside to avoid DB calls
    mock_search = AsyncMock()
    mock_search.search_drug_smart.return_value = {
        "data": {
            "ten_thuoc": "Panadol",
            "so_dang_ky": "VN-123", 
            "is_verified": 1
        },
        "confidence": 1.0,
        "source": "MockDB"
    }
    
    # Inject mock
    identification_service.search_service = mock_search
    
    async def test_batch():
        res = await identification_service.process_batch(["Panadol"])
        print(f"Batch Result: {res}")
        assert len(res) == 1
        assert res[0]['official_name'] == "Panadol"
        assert res[0]['is_duplicate'] is False
        
    asyncio.run(test_batch())
    print("✅ process_batch logic verification passed.")

    print("\n🎉 REFACTOR PHASE 2 PASSED!")

except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    sys.exit(1)
