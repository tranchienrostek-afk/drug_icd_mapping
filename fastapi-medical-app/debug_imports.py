import sys
import os

print(f"Python Path: {sys.path}")
print(f"CWD: {os.getcwd()}")

try:
    import app
    print("✅ import app: SUCCESS")
    print(f"app file: {app.__file__}")
except ImportError as e:
    print(f"❌ import app: FAILED ({e})")

try:
    from app.service.consultation_service import ConsultationService
    print("✅ import ConsultationService: SUCCESS")
except ImportError as e:
    print(f"❌ import ConsultationService: FAILED ({e})")

try:
    from app.mapping_drugs.service import ClaimsMedicineMatchingService
    print("✅ import ClaimsMedicineMatchingService: SUCCESS")
except ImportError as e:
    print(f"❌ import ClaimsMedicineMatchingService: FAILED ({e})")
