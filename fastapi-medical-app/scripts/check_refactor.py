
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("1. Importing app.services...")
    from app.services import DrugDbEngine
    print("✅ app.services imported successfully.")

    print("2. Initializing DrugDbEngine (Facade)...")
    db = DrugDbEngine()
    print("✅ DrugDbEngine initialized.")

    print("3. Checking Sub-Services...")
    assert db.db_core is not None, "DatabaseCore failed"
    assert db.repo is not None, "DrugRepository failed"
    assert db.search_service is not None, "DrugSearchService failed"
    assert db.approval_service is not None, "DrugApprovalService failed"
    print("✅ All Sub-Services linked.")

    print("3b. Checking EtlService...")
    from app.service.etl_service import EtlService
    etl = EtlService()
    assert etl is not None, "EtlService failed to init"
    print("✅ EtlService initialized.")

    async def test_async_method():
        print("4. Testing Async Method (get_drug_by_id)...")
        # Ensure we don't crash even if DB is empty
        res = await db.get_drug_by_id(1)
        print(f"✅ Async call returned: {res}")

    # Run async test
    asyncio.run(test_async_method())

    print("\n🎉 REFACTOR VERIFICATION PASSED!")

except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)
except AssertionError as e:
    print(f"❌ AssertionError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    sys.exit(1)
