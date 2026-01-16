
import sys
import os
import asyncio
from unittest.mock import AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("1. Importing app.api.consult...")
    from app.api.consult import router, consultation_service
    print("✅ app.api.consult imported successfully.")

    print("2. Testing ConsultationService instantiation...")
    assert consultation_service is not None
    print("✅ consultation_service is present in API module.")

    print("3. Testing consult_hybrid (Mocked)...")
    
    # Mock methods
    consultation_service.check_knowledge_base = MagicMock(return_value={
        "validity": "valid", 
        "role": "main", 
        "explanation": "Mock KB", 
        "source": "Mock"
    })
    
    # Mock items
    class MockItem:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    
    class MockDiagnosis:
        def __init__(self, code, name, type):
            self.code = code
            self.name = name
            self.type = type

    async def test_consult():
        items = [MockItem("1", "DrugA")]
        diagnoses = [MockDiagnosis("A00", "DiseaseA", "MAIN")]
        
        # Override internals for testing without DB
        res = await consultation_service.consult_integrated(items, diagnoses)
        print(f"Consult Result: {res}")
        assert len(res) == 1
        assert res[0]['name'] == "DrugA"
        
    from unittest.mock import MagicMock
    asyncio.run(test_consult())
    print("✅ consult_hybrid logic verification passed.")

    print("\n🎉 REFACTOR CONSULT PY PASSED!")

except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    sys.exit(1)
